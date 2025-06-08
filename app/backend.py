from fastapi import FastAPI
from pydantic import BaseModel
from scripts.rag_pipeline import get_rag_response

app = FastAPI()

class Query(BaseModel):
    question: str
    grade: str
    subject: str

@app.post("/ask")
def ask(query: Query):
    answer = get_rag_response(query.question, query.grade, query.subject)
    return {"answer": answer}