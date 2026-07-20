from langchain_community.document_loaders import PyPDFLoader

def ingest_transcript(pdf_path: str) -> str:

    pages = PyPDFLoader(pdf_path).load()
    output = "\n\n".join(p.page_content for p in pages)
    return output 