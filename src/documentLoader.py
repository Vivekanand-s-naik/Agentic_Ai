import warnings

warnings.filterwarnings("ignore")
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader, JSONLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader

from typing_extensions import List, Any
from pathlib import Path

def load_all_docs(data_dir: str)->List[Any]:
    data_path = Path(data_dir).resolve()
    
    pdf_files = list(data_path.rglob("*.pdf"))
    docx_files = list(data_path.rglob("*.docx"))
    txt_files = list(data_path.rglob("*.txt"))
    json_files = list(data_path.rglob("*.json"))
    excel_files = list(data_path.rglob("*.xlsx"))
    
    documents = []
    # Load all pdf file
    for pdf in pdf_files:
        print(f"[INFO] Loading PDF: {pdf.name}...")
        pdf_loader = PyMuPDFLoader(str(pdf))
        loaded = pdf_loader.load()
        print(f"[SUCCESS] Extracted {len(loaded)} pages/chunks from {pdf.name}")
        documents.extend(loaded)
        
    # load the docx file
    for docx in docx_files:
        print(f"[INFO] Loading DOCX: {docx.name}...")
        docx_loader = Docx2txtLoader(str(docx))
        loaded = docx_loader.load()
        print(f"[SUCCESS] Extracted {len(loaded)} chunks from {docx.name}")
        documents.extend(loaded)
    
    # load Text file 
    for txt in txt_files:
        print(f"[INFO] Loading TXT: {txt.name}...")
        txt_loader = TextLoader(str(txt), encoding="utf-8")
        loaded = txt_loader.load()
        print(f"[SUCCESS] Extracted {len(loaded)} chunks from {txt.name}")
        documents.extend(loaded)
        
    # Load json file
    for json in json_files:
        print(f"[INFO] Loading JSON: {json.name}...")
        json_loader = JSONLoader(str(json), jq_schema=".", text_content=False)
        loaded = json_loader.load()
        print(f"[SUCCESS] Extracted {len(loaded)} chunks from {json.name}")
        documents.extend(loaded)    

    # load excel file
    for excel in excel_files:
        print(f"[INFO] Loading Excel: {excel.name}...")
        excel_loader = UnstructuredExcelLoader(str(excel))
        loaded = excel_loader.load()
        print(f"[SUCCESS] Extracted {len(loaded)} chunks from {excel.name}")
        documents.extend(loaded)

    
    return documents

# res = load_all_docs("./doc_files")
# print(res)