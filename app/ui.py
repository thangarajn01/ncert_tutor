import streamlit as st
import requests

st.set_page_config(page_title="NCERT Tutor", layout="centered")

st.title("📘 NCERT Tutor")
st.markdown("Ask questions or take a quiz based on your subject and grade.")

# Mode selection
mode = st.radio("Choose Mode:", ["QA", "Quiz"])

# Grade, Subject, Chapter
grade = st.selectbox("Select Grade:", ["11", "12"])
subject = st.selectbox("Select Subject:", ["Physics", "Computer Science"])
chapter = st.text_input("Enter Chapter (optional)")

# ---------------- QA MODE ---------------- #
if mode == "QA":
    question = st.text_area("Ask your question:")
    if st.button("Get Answer"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post(
                    "http://localhost:8000/qa",
                    json={
                        "query": question,
                        "grade": grade,
                        "subject": subject,
                        "chapter": chapter
                    },
                    timeout=30
                )
                res.raise_for_status()
                answer = res.json().get("answer", "No answer received.")
                st.markdown(f"**Answer:** {answer}")
            except Exception as e:
                st.error("❌ Sorry, an error occurred while generating your answer.")
                st.exception(e)

# ---------------- QUIZ MODE ---------------- #
elif mode == "Quiz":
    if st.button("Generate Quiz"):
        with st.spinner("Generating quiz..."):
            try:
                res = requests.post(
                    "http://localhost:8000/quiz",
                    json={
                        "grade": grade,
                        "subject": subject,
                        "chapter": chapter
                    },
                    timeout=60
                )
                res.raise_for_status()
                quiz_data = res.json().get("quiz", [])

                if not quiz_data:
                    st.warning("No quiz generated.")
                else:
                    st.session_state["quiz_data"] = quiz_data
                    st.session_state["quiz_submitted"] = False
            except Exception as e:
                st.error("❌ Failed to generate quiz.")
                st.exception(e)

    # Display quiz questions
    if "quiz_data" in st.session_state and not st.session_state.get("quiz_submitted", False):
        quiz_data = st.session_state["quiz_data"]

        st.markdown("### Quiz")
        for idx, q in enumerate(quiz_data):
            st.markdown(f"**Q{idx+1}:** {q['question']}")
            option_display = [
                f"{k}. {v}" for k, v in q["options"].items()
            ] if "options" in q and isinstance(q["options"], dict) else []
            
            # Let the radio widget manage its session state
            selected_display = st.radio(
                f"Select your answer for Q{idx+1}",
                option_display,
                key=f"q{idx}_answer"
            )

            # Extract just the letter A/B/C/D (without writing to session_state directly)
            if selected_display:
                selected_letter = selected_display.split(".")[0].strip().upper()
                st.session_state[f"user_selected_{idx}"] = selected_letter
            else:
                st.session_state[f"user_selected_{idx}"] = None

        if st.button("Submit Answers"):
            st.session_state["quiz_submitted"] = True

    # Evaluate quiz
    if st.session_state.get("quiz_submitted", False):
        quiz_data = st.session_state["quiz_data"]
        score = 0
        st.markdown("## Results")
        for idx, q in enumerate(quiz_data):
            selected = st.session_state.get(f"user_selected_{idx}", "")
            correct = q["answer"].strip().upper()
            selected_text = q["options"].get(selected, "")
            correct_text = q["options"].get(correct, "")

            if selected == correct:
                st.success(f"Q{idx+1}: ✅ Correct! ({selected}) {selected_text}")
                score += 1
            else:
                st.error(
                    f"Q{idx+1}: ❌ Incorrect.\n\n"
                    f"Your Answer: ({selected}) {selected_text}\n"
                    f"Correct Answer: ({correct}) {correct_text}"
                )

        st.markdown(f"**Your score: {score} / {len(quiz_data)}**")

        if st.button("Take Another Quiz"):
            for key in list(st.session_state.keys()):
                if key.startswith("q") or key in ["quiz_data", "quiz_submitted"]:
                    del st.session_state[key]
