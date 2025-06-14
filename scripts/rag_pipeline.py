from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


from fastapi.responses import JSONResponse
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.runnables import RunnableSequence 


import re, pprint

from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever()

def get_rag_response(query: str, grade: str, subject: str):
    try:
        print(f"[QUERY] Grade: {grade}, Subject: {subject}, Question: {query}")

        # Setup retriever with metadata filters
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4,
                "filter": {
                    "grade": grade,
                    "subject": subject.lower(),
                }
            }
        )

        # Use updated LLM import (langchain-openai)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Define prompt with placeholders
        prompt = PromptTemplate.from_template("""
        You are a knowledgeable tutor for grade {grade} in {subject}.
        Use only the provided context to answer the question below.
        If the context does not contain the answer, say "I don't know based on the given materials."

        Context:
        {context}

        Question:
        {input}
        """)

        # Fill static vars (grade, subject) at compile time
        final_prompt = prompt.partial(grade=grade, subject=subject)

        # Build RAG chain
        combine_docs_chain = create_stuff_documents_chain(llm, final_prompt)
        rag_chain: RunnableSequence = create_retrieval_chain(retriever, combine_docs_chain)

        # Run the RAG chain with just `query` as input
        result = rag_chain.invoke({"input": query})
        #print("=== RAG Chain Result ===")
        #pprint.pprint(result)

        # Extract the final answer (always under key "answer")
        raw_answer = result.get("answer", "No answer found.")
        answer = raw_answer.get("answer") if isinstance(raw_answer, dict) else raw_answer

        # Extract sources
        simplified_sources = []
        for doc in result.get("context", []):
            metadata = doc.metadata
            page_content = doc.page_content if hasattr(doc, 'page_content') else "No content available"
            print(f"Source doc metadata: {metadata}")
            simplified_sources.append({
                "filename": metadata.get("source", "Untitled"),
                "page number": metadata.get("page", "#"),
                "page content": page_content[:300]  # Limit to first 200 chars for brevity),
            })

        return {
            "answer": answer,
            "sources": simplified_sources
        }

    except Exception as e:
        print(f"[ERROR] RAG pipeline failed: {e}")
        return {
            "answer": "Sorry, an error occurred while generating your answer.",
            "sources": []
        }

    

def generate_quiz(grade, subject, chapter=None, num_questions=5):
    llm = ChatOpenAI(temperature=0, model='gpt-4o-mini')
    try:
        prompt = f"""
        Generate {num_questions} multiple choice questions (MCQs) for grade {grade} {subject}.
        Each question should have 4 options (A to D) and indicate the correct answer as 'Answer: <option>' after each question.
        Format:
        Q1. What is ...?
        A. ...
        B. ...
        C. ...
        D. ...
        Answer: A
        """
        return llm.invoke(prompt).content
    except Exception as e:
        print(f"[ERROR] Quiz generation failed: {e}")
        return "Error generating quiz."
    
def parse_quiz_text(raw_text: str) -> list[dict]:
    questions = re.split(r'Q\d+:', raw_text)[1:]  # split by Q1:, Q2:, etc.
    blocks = raw_text.split("Q")[1:]  # Each block starts with "1:", "2:", ...
    parsed_quiz = []

    for block in blocks:
        try:
            question_part = block.split("A.")[0].strip()
            options_part = re.findall(r'[A-D]\..+?(?=(?:[A-D]\.|Answer:))', block, re.DOTALL)
            options = {}
            for opt in options_part:
                key = opt.strip()[0]
                val = opt.strip()[2:].strip()
                options[key] = val

            answer_match = re.search(r'Answer:\s*([A-D])', block)
            answer = answer_match.group(1) if answer_match else ""

            parsed_quiz.append({
                "question": question_part,
                "options": options,
                "answer": answer
            })
        except Exception as e:
            print(f"Error parsing block: {block[:30]}... — {e}")

    return parsed_quiz