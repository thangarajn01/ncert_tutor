import streamlit as st
import requests

st.title("NCERT RAG Tutor")

grade = st.selectbox("Select Grade", ["11", "12"])
subject = st.selectbox("Select Subject", ["physics", "computer"])
question = st.text_input("Ask your question")

if st.button("Submit"):
    response = requests.post("http://localhost:8000/ask", json={
        "question": question,
        "grade": grade,
        "subject": subject
    })
    st.write("Answer:", response.json().get("answer", "Error getting answer"))
