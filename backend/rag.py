import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


DATA_DIR = "data"
_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
_index_cache: dict[int, FAISS] = {}


def init_db(chunks: list[str], doc_id: int, openai_api_key: str):
    """Embed chunks and save a FAISS index for the given document."""

    os.makedirs(DATA_DIR, exist_ok=True)
    index_path = os.path.join(DATA_DIR, f"faiss_index_{doc_id}")

    if os.path.exists(index_path):
        print(f"[cache hit] Index for doc {doc_id} already exists, skipping")
        return

    docs = [Document(page_content=chunk) for chunk in chunks]

    print(f"[embedding] Embedding {len(docs)} chunks for doc {doc_id}...")
    vector_store = FAISS.from_documents(docs, _embeddings)

    print(f"[saving] Writing FAISS index to {index_path}")
    vector_store.save_local(index_path)
    del vector_store
    print(f"[saved] Done")


def load_db(doc_id: int, openai_api_key: str) -> FAISS:
    """Load a FAISS index for the given document, caching it in memory."""

    if doc_id not in _index_cache:
        index_path = os.path.join(DATA_DIR, f"faiss_index_{doc_id}")
        _index_cache[doc_id] = FAISS.load_local(index_path, _embeddings, allow_dangerous_deserialization=True)
        print(f"[cache miss] Loaded index for doc {doc_id} from disk")
    else:
        print(f"[cache hit] Index for doc {doc_id} already in memory")

    return _index_cache[doc_id]


def query(question: str, doc_id: int, openai_api_key: str) -> str:
    """Retrieve relevant chunks and answer the question using the LLM."""

    vector_store = load_db(doc_id, openai_api_key)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    prompt = PromptTemplate.from_template("""
You are a helpful assistant that answers questions about a student's academic transcript.
Use only the context provided to answer. If the answer is not in the context, say you don't know.

Context:
{context}

Question: {question}

Answer:""")

    llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", temperature=0)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(question)
