from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

from dotenv import load_dotenv
load_dotenv()

def get_rag_response(query: str, grade: str, subject: str) -> str:
    try:
        print(f"[QUERY] Grade: {grade}, Subject: {subject}, Question: {query}")

        embedding = OpenAIEmbeddings(model='text-embedding-3-small')
        vectorstore = FAISS.load_local("vector_store", embedding, allow_dangerous_deserialization=True)

        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4,
                "filter": {
                    "grade": grade,
                    "subject": subject.lower()
                }
            }
        )

        llm = ChatOpenAI(temperature=0, model='gpt-4o-mini')
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=False
        )

        result = rag_chain.run(query)
        return result

    except Exception as e:
        print(f"[ERROR] RAG pipeline failed: {e}")
        return "Sorry, an error occurred while generating your answer."
