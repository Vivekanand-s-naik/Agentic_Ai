import warnings

warnings.filterwarnings("ignore")
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader, JSONLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader

from typing_extensions import List, Any
from pathlib import Path

def load_all_docs(data_dir: str)->List[Any]:
    data_path = Path(data_dir).resolve()
    
    pdf_files = data_path.rglob("*.pdf")
    docx_files = data_path.rglob("*.docx")
    txt_files = data_path.rglob("*.txt")
    json_files = data_path.rglob("*.json")
    excel_files = data_path.rglob("*.xlsx")
    
    documents = []

    # Load all pdf file
    for pdf in pdf_files:
        pdf_loader = PyMuPDFLoader(str(pdf))
        loaded = pdf_loader.load()
        documents.extend(loaded)
        
    # load the docx file
    for docx in docx_files:
        docx_loader = Docx2txtLoader(str(docx))
        loaded = docx_loader.load()
        documents.extend(loaded)
    
    # load Text file 
    for txt in txt_files:
        txt_loader = TextLoader(str(txt))
        loaded = txt_loader.load()
        documents.extend(loaded)
        
    # Load json file
    for json in json_files:
        json_loader = JSONLoader(str(json), jq_schema=".", text_content=False)
        loaded = json_loader.load()
        documents.extend(loaded)    
    # load excel file
    for excel in excel_files:
        excel_loader = UnstructuredExcelLoader(str(excel))
        loaded = excel_loader.load()
        documents.extend(loaded) 
    
    return documents

res = load_all_docs("../doc_files")
print(res)