from fastapi import APIRouter, UploadFile, Form, Response
from typing import Optional
from middleware.parser.query import parse_pdf

from langchain_chroma import Chroma 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

router = APIRouter()

@router.post('/parse')
async def parse(
    response: Response,
    file: Optional[UploadFile] = Form(None),
    message: str = Form(...),
):
    user_query = {
        "message": message,
        "has_file": False 
    }

    if file:
        file_bytes = await file.read()
        parse_pdf(file_bytes) # Middleware
        user_query["has_file"] = True 
   
    llm = OllamaLLM(model="phi3", base_url='http://ollama:11434')
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url='http://ollama:11434')

    filters = get_filters_with_llm(message, llm)
    multi_filter = handle_multiple_filter_conditions(filters)

    vectorstore = Chroma(
        collection_name='student-transcript-data',
        embedding_function=embeddings,
    )

    retriever = None 
    if filters:
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 10,
                "filter": multi_filter 
            }
        )
    else:
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 50
            }
        )

    prompt = ChatPromptTemplate.from_template("""
                                              
            Here is information provided in the database:

            {context}

            Question: {question}

            You are then responsible for determining what rules to follow based on the question
                                              
            1. If asking about CLASSES/COURSES:
            - Extract ONLY the course codes
            - Format: CSE 101, POL 102, AMS 210
            - No bullet points, dashes, or chunk IDs

            2. If asking about GRADES:
            - List each course with its grade
            - Format: CSE 101: A, POL 102: B+, AMS 210: A-
            - No bullet points, dashes, or chunk IDs

            3. If asking about POINTS:
            - List each course with points earned
            - Format: CSE 101: 12.0 points, POL 102: 11.5 points
            - No bullet points, dashes, or chunk IDs

            4. For ANY OTHER question:
            - Provide the relevant information naturally
            - Be concise and clear
            - If you don't know the answer, then say you don't know
            - Do NOT provide more information if you are uncertain. 
                                                
            Please answer based on ALL the database information provided.                        
    """)

    chain = (
        {"context": retriever,  "question": RunnablePassthrough() }
        | prompt
        | llm
        | StrOutputParser()
    )

    llm_answer = chain.invoke(message)
    print(llm_answer)

    response.status_code = 200
    return {"message": llm_answer}


# Helper function that makes a call to another LLM to extract important data 
def get_filters_with_llm(query, llm):

    filters = {}

    prompt = ChatPromptTemplate.from_template("""
        You are a filter extraction system. Extract specific filters from the user's query and return them as a JSON object.

        FILTER RULES:
        1. class: If the user mentions a course in the format of 3 letters followed by 3 digits
        - Examples: "CSE 101", "ITS 102", "MATH 125"
        - JSON format: "class": "CSE 101"
        - Please be sure to remove chunk ids, dots, and dashes

        2. semester: If the user mentions a semester (Fall, Winter, Spring, Summer) followed by a 4-digit year
        - Examples: "Spring 2023", "Fall 2024", "Summer 2022"
        - JSON format: "semester": "Spring 2023"
        - Please be sure to remove chunk ids, dots, and dashes

        3. studentId: If the user mentions a 9-digit student ID number
        - Examples: "student 113227753", "ID 123456789"
        - JSON format: "studentId": "113224953"
        - Please be sure to remove chunk ids, dots, and dashes

        4. grade: If the user mentions a specific letter grade
        - Examples: "grade A", "got a B+", "received C-"
        - JSON format: "grade": "A" or "grade": "B+"
        - Please be sure to remove chunk ids, dots, and dashes
                                              
        IMPORTANT:
        - Only include filters that are EXPLICITLY mentioned in the query
        - Return an empty object {{}} if no filters are found
        - Course codes should be uppercase
        - Capitalize the first letter of semester (e.g., "Spring" not "spring")

        Query: {query}

        Return ONLY valid JSON, nothing else.

        JSON:""")

    chain = prompt | llm | JsonOutputParser()

    try:
        filters = chain.invoke({"query": query})
        return filters if filters else None 
    except:
        return None 

# Ha
def handle_multiple_filter_conditions(filters):
    if not filters:
        return None 
    
    if len(filters) == 1:
        return filters

    conditions = [{k: v} for k, v in filters.items()]
    return {"$and": conditions}