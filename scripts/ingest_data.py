import os, json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


def load_and_split_all(data_dir="data/"):
    all_docs = []

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)

                # Extract grade, subject, chapter from path
                parts = file_path.split(os.sep)
                try:
                    grade = parts[-3].replace("grade_", "")  # e.g., '11'
                    subject = parts[-2].lower()              # e.g., 'physics'
                    chapter = os.path.splitext(file)[0].lower()  # e.g., 'chapter1'
                    print(f"Grade: {grade}, Subject: {subject}, Chapter: {chapter}")
                except IndexError:
                    print(f"[WARNING] Skipping improperly structured path: {file_path}")
                    continue

                print(f"[INFO] Processing → Grade {grade}, Subject {subject}, Chapter {chapter}")

                try:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()

                    # Add metadata to each page
                    for doc in docs:
                        doc.metadata.update({
                            "grade": grade,
                            "subject": subject,
                            "chapter": chapter
                        })

                    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                    split_docs = splitter.split_documents(docs)
                    all_docs.extend(split_docs)

                except Exception as e:
                    print(f"[ERROR] Failed to process {file_path}: {e}")
    
    return all_docs

if __name__ == "__main__":
    docs = load_and_split_all("data/")
    print(f"Total chunks created: {len(docs)}")