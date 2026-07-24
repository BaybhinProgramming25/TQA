import os
import logging

from dotenv import load_dotenv
from helpers.store import transcripts

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

logger = logging.getLogger(__name__)
openai_api_key = os.environ["OPENAI_API_KEY"]


CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     'Determine if the question can be answered from a student\'s academic '
     'transcript. Transcripts contain: the student\'s name, student ID, '
     'program, major, degree, catalog year, academic standing, honors, and '
     'their full course history including courses, grades, GPA, credits, '
     'and semesters.\n'
     'Answer only "yes" or "no". Nothing else.'),
    ("human", "{question}"),
])

TRANSCRIPT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that answers questions about a \
student's academic transcript. Use only the context provided. The context \
contains the student's COMPLETE course history — every course and every \
semester. Answer directly as if talking to the student. Start with the \
answer. Be concise — usually 1-2 sentences, but list multiple courses or \
semesters in full when asked.

Only report facts that are EXPLICITLY stated in the context. Do not infer, \
calculate, or assume conclusions the document does not state. For example: \
if a semester's GPA seems high, do NOT conclude the student made the \
Dean's List unless the transcript explicitly says "Dean's List" for that \
semester. If asked about honors, awards, or academic standing, report only \
what is literally written.

If the user asks about a course that does not appear in the context, \
respond: "<course> could not be found in your transcript."
If the user asks about a semester that does not appear in the context, \
respond: "Your transcript has no records for <semester>. It covers \
<first semester> through <last semester>."
If the user asks about their name or ID number, provide them with \
that information ONLY if it appears in the context. If it does not \
appear, say: "That information is not in your transcript."
For ANY other information that does not appear in the context, say it \
is not in the transcript. Never guess or fill in missing information.

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

llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", temperature=0)
transcript_chain = TRANSCRIPT_PROMPT | llm | StrOutputParser()


async def query_stream(question: str, user_email: str, history: list = []):
    """Classify the question, then stream the answer with or without RAG."""

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

    transcript_info = transcripts.get(user_email)

    if not transcript_info:                                   
        yield ("token", "I don't have your transcript yet — upload it first!")
        return

    async for chunk in transcript_chain.astream({"context": transcript_info, "question": question, "history": history}):
        yield ("token", chunk)

