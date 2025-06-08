from dotenv import load_dotenv
load_dotenv()

from ingest_data import load_and_split_all
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

if __name__ == "__main__":
    print("[INFO] Loading and splitting all documents...")
    all_docs = load_and_split_all("data/")

    if not all_docs:
        print("[WARNING] No documents found. Please check your data directory.")
    else:
        print(f"[INFO] Creating vector store with {len(all_docs)} chunks...")
        embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
        vectorstore = FAISS.from_documents(all_docs, embeddings)
        vectorstore.save_local("vector_store")
        print("[SUCCESS] Vector store saved to 'vector_store/'")
