import os
import logging
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)


DATA_DIR = os.getenv("DATA_DIR", "data")
_embeddings: OpenAIEmbeddings | None = None
_index_cache: dict[str, FAISS] = {}


def get_embeddings(openai_api_key: str) -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(api_key=openai_api_key, model="text-embedding-3-large")
    return _embeddings


def init_db(chunks: list[tuple[str, dict]], index_key: str, openai_api_key: str):
    """Embed chunks and save a FAISS index for the given document."""

    os.makedirs(DATA_DIR, exist_ok=True)
    index_path = os.path.join(DATA_DIR, f"faiss_index_{index_key}")

    if os.path.exists(index_path):
        logger.info("Index for %s already exists, skipping", index_key)
        return

    docs = [Document(page_content=chunk, metadata=metadata) for chunk, metadata in chunks]

    logger.info("Embedding %d chunks for %s", len(docs), index_key)
    vector_store = FAISS.from_documents(docs, get_embeddings(openai_api_key))

    logger.info("Writing FAISS index to %s", index_path)
    vector_store.save_local(index_path)
    del vector_store
    logger.info("FAISS index saved for %s", index_key)




def load_db(index_key: str, openai_api_key: str) -> FAISS:
    """Load a FAISS index for the given document, caching it in memory."""

    if index_key not in _index_cache:
        index_path = os.path.join(DATA_DIR, f"faiss_index_{index_key}")
        _index_cache[index_key] = FAISS.load_local(index_path, get_embeddings(openai_api_key), allow_dangerous_deserialization=True)
        logger.info("Loaded index for %s from disk", index_key)
    else:
        logger.info("Index for %s already in memory", index_key)

    return _index_cache[index_key]




def delete_index(index_key: str):
    """Remove a FAISS index from disk and evict it from the in-memory cache."""

    index_path = os.path.join(DATA_DIR, f"faiss_index_{index_key}")
    if os.path.exists(index_path):
        import shutil
        shutil.rmtree(index_path)
        logger.info("Removed FAISS index at %s", index_path)

    _index_cache.pop(index_key, None)




CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a classifier. Determine if the question is related to an academic transcript, courses, grades, GPA, credits, semesters, or academic records.
Answer only "yes" or "no". Nothing else."""),
    ("human", "{question}"),
])

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that answers questions about a \
student's academic transcript. Use only the context provided. The context \
contains the student's COMPLETE course history — every course and every \
semester. Answer directly as if talking to the student. Start with the \
answer. Be concise — usually 1-2 sentences, but list multiple courses or \
semesters in full when asked.

If the user asks about a course that does not appear in the context, \
respond: "<course> could not be found in your transcript."
If the user asks about a semester that does not appear in the context, \
respond: "Your transcript has no records for <semester>. It covers \
<first semester> through <last semester>."
Never say "I don't know."

Context:
{context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a friendly assistant. Answer conversationally and concisely in 1-2 sentences."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """Given the chat history, rewrite the user's latest question so it \
makes complete sense on its own, with no pronouns or vague references \
like "it", "those courses", "that semester", "what about...". \
Fill in the specific courses, semesters, or topics the user is referring to, \
based on the history. Do NOT answer the question. Do NOT add new meaning. \
If the question already makes complete sense on its own, return it \
exactly unchanged. Return ONLY the question, nothing else."""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])


async def query_stream(question: str, index_key: str, openai_api_key: str, history: list = []):
    """Classify the question, then stream the answer with or without RAG."""

    llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", temperature=0)

    standalone = question 
    if history:
        rewriter_chain = REWRITE_PROMPT | llm | StrOutputParser()
        result = (await rewriter_chain.ainvoke({"question": question, "history": history})).strip()

        if result:
            standalone = result 

    classify_chain = CLASSIFY_PROMPT | llm | StrOutputParser()
    classification = (await classify_chain.ainvoke({"question": standalone})).strip().lower()
    is_transcript_question = classification.startswith("yes")

    if not is_transcript_question:
        yield ("sources", [])
        chat_chain = CHAT_PROMPT | llm | StrOutputParser()
        async for chunk in chat_chain.astream({"question": question, "history": history}):
            yield ("token", chunk)
        return

    vector_store = load_db(index_key, openai_api_key)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    retrieved_docs = retriever.invoke(question)
    top_page = retrieved_docs[0].metadata.get("page") if retrieved_docs else None
    pages = [top_page] if top_page else []
    yield ("sources", pages)

    chain = (
        {
            "context": lambda x: retrieved_docs,
            "question": lambda x: x["question"],
            "history": lambda x: x["history"],
        }
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    async for chunk in chain.astream({"question": question, "history": history}):
        yield ("token", chunk)

