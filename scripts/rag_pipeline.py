from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import re

from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever()

def get_rag_response(query: str, grade: str, subject: str) -> str:
    try:
        template = ("You are an NCERT tutor for grade {grade} and subject {subject}. "
                    "Answer the question using the provided context.\nQuestion: {question}")
        prompt = PromptTemplate.from_template(template)
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=False
        )
        return chain.run({"question": query, "grade": grade, "subject": subject})
    except Exception as e:
        print(f"[ERROR] RAG pipeline failed: {e}")
        return "Sorry, an error occurred while generating your answer."


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