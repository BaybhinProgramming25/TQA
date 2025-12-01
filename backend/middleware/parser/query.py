import sys 
import os 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fitz
from middleware.parser.semestermapper.GetMapping import get_sem_mapping
from middleware.parser.contentmapper.GetCourses import get_content_from_each_sem
from middleware.chunking.main import construct_chroma

def parse_pdf(file_bytes):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    pdf_pages_list = []
    for page in doc:
        text = page.get_text("text").strip("").split("\n")
        pdf_pages_list.extend(text)

    # Get the sem_mapping
    sm_ll = get_sem_mapping(pdf_pages_list)
    description_list, metadata_list  = get_content_from_each_sem(sm_ll, pdf_pages_list)

    # Then we want to add it to chroma 
    construct_chroma(description_list, metadata_list)
    doc.close()
 