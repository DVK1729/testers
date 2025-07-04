from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.callbacks import tracing_v2_enabled
import os
from dotenv import load_dotenv

load_dotenv()

def ingest(file_path: str, index_path: str = "faiss_index"):
    with tracing_v2_enabled(project_name="AI Market Analyst - Ingestion"):
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(docs)

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(index_path)
        print("✅ Ingestion complete.")

if __name__ == "__main__":
    ingest("./internal_market_research_docs.pdf")
