from langchain_community.document_loaders import DirectoryLoader    

loader = DirectoryLoader("./doc_files")
content = loader.load()
print(content)
