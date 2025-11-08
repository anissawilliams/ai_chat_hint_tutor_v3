from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import json
import os

chunks_path = "baeldung_scraper/chunks.json"
index_path = "baeldung_scraper/chroma_index"

with open(chunks_path, "r") as f:
    chunks = json.load(f)

docs = [Document(page_content=chunk["text"]) for chunk in chunks]
from langchain.embeddings import FakeEmbeddings
embeddings = FakeEmbeddings(size=768)

Chroma.from_documents(docs, embedding=embeddings, persist_directory=index_path)

print("✅ Chroma index built at:", index_path)
