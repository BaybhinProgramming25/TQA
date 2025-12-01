import tiktoken 
import chromadb

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


# Chunk by tokens 
def chunk_tokens(tokens_list, chunk_size=500, overlap=0):

    chunks = []
    for tokens in tokens_list:
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk = tokens[i:i + chunk_size]
            chunks.append(chunk)

            if i + chunk_size >= len(tokens):
                break 

    return chunks 


def chunk_data(student_data_array):
  
    encoding = tiktoken.get_encoding("cl100k_base")
    # Next, we tokenize the text
    tokens_list = []
    for text in student_data_array:
        tokens = encoding.encode(text)
        tokens_list.append(tokens)
    token_chunks = chunk_tokens(tokens_list, chunk_size=500, overlap=0)

    # Now view the chunk tokens 
    text_chunks = []
    for token_chunk in token_chunks:
        text = encoding.decode(token_chunk)
        text_chunks.append(text)
    return text_chunks


def construct_chroma(description_list: list, metadata_list: list):

    collection_str = 'student-transcript-data'
    client = chromadb.EphemeralClient()

    try:
        client.delete_collection(name=collection_str)
    except:
        print("Couldn't find collection. Making new one... ")
        client.create_collection(name=collection_str)
    
    #2) Chunk the required data 
    data_chunks = chunk_data(description_list)

    #3) Add the newly created chunk data into the database and verify
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url='http://ollama:11434')

    vectorstore = Chroma(
        collection_name=collection_str,
        embedding_function=embeddings,
    )
    
    # Make documents from chunks 
    documents = [
        Document(
            page_content=chunk,
            metadata={
                **metadata,
                "chunk_id": i
            }
        )
        for i, (chunk, metadata) in enumerate(zip(data_chunks, metadata_list))
    ]
    vectorstore.add_documents(documents)
