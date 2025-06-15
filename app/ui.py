import streamlit as st
import requests, json
import streamlit.components.v1 as components


st.set_page_config(page_title="NCERT Tutor", layout="centered")

st.title("📘 NCERT Tutor")
st.markdown("Ask questions or take a quiz based on your subject and grade.")

# Mode selection
mode = st.radio("Choose Mode:", ["QA", "Quiz"])

# Grade, Subject, Chapter
grade = st.selectbox("Select Grade:", ["11", "12"])
subject = st.selectbox("Select Subject:", ["Physics", "Computer"])

def renaaader_markdown_with_mathjax(markdown_text: str):
    # Escape special characters safely
    safe_text = markdown_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("</script>", "<\\/script>")

    html_template = f"""
    <html>
    <head>
        <!-- Markdown parser -->
        <script src="https://cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>

        <!-- MathJax Config -->
        <script>
        window.MathJax = {{
          tex: {{
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
          }},
          svg: {{ fontCache: 'global' }}
        }};
        </script>

        <!-- MathJax script -->
        <script type="text/javascript" async
            src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
        </script>
    </head>
    <body>
        <div id="content" style="font-size: 16px; line-height: 1.6; padding: 10px;"></div>

        <script>
            function render() {{
                const md = window.markdownit({{ html: true }});
                const rawText = `{safe_text}`;
                const htmlContent = md.render(rawText);
                const container = document.getElementById("content");
                container.innerHTML = htmlContent;

                // Wait for MathJax to be ready
                if (window.MathJax && window.MathJax.typesetPromise) {{
                    MathJax.typesetPromise([container]).catch(function (err) {{
                        console.error("MathJax typeset failed: ", err);
                    }});
                }}
            }}

            // Poll until markdown-it is available
            if (window.markdownit) {{
                render();
            }} else {{
                const interval = setInterval(() => {{
                    if (window.markdownit) {{
                        clearInterval(interval);
                        render();
                    }}
                }}, 50);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_template, height=600, scrolling=True)


def render_markdown_with_mathjax(markdown_text: str):
    # Escape the text safely using JSON (handles backslashes, quotes, etc.)
    safe_json_text = json.dumps(markdown_text)

    html_template = f"""
    <html>
    <head>
        <!-- Markdown Parser -->
        <script src="https://cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>

        <!-- MathJax Configuration -->
        <script>
        window.MathJax = {{
          tex: {{
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
          }},
          svg: {{ fontCache: 'global' }}
        }};
        </script>

        <!-- MathJax Script -->
        <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </head>
    <body>
        <div id="content" style="font-size: 16px; line-height: 1.6; padding: 10px;"></div>

        <script>
            function render() {{
                const md = window.markdownit({{ html: true }});
                const rawText = {safe_json_text};  // ✅ Safe-escaped input
                const htmlContent = md.render(rawText);
                const container = document.getElementById("content");
                container.innerHTML = htmlContent;

                if (window.MathJax && window.MathJax.typesetPromise) {{
                    MathJax.typesetPromise([container]).catch(err => {{
                        console.error("MathJax typeset failed:", err);
                    }});
                }}
            }}

            if (window.markdownit) {{
                render();
            }} else {{
                const interval = setInterval(() => {{
                    if (window.markdownit) {{
                        clearInterval(interval);
                        render();
                    }}
                }}, 50);
            }}
        </script>
    </body>
    </html>
    """

    components.html(html_template, height=900, scrolling=True)

# ---------------- QA MODE ---------------- #
if mode == "QA":
    question = st.text_area("Ask your question:")
    if st.button("Get Answer"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post(
                    "http://localhost:8000/ask",
                    json={
                        "question": question,
                        "grade": grade,
                        "subject": subject,
                    },
                    timeout=30
                )
                res.raise_for_status()
                res_data = res.json()
                # Ensure the answer is a string
                raw_answer = res_data.get("answer", "No answer received.")
                answer = raw_answer.get("answer") if isinstance(raw_answer, dict) else raw_answer
                sources = raw_answer.get("sources", [])
                
                st.markdown("### Answer")
                render_markdown_with_mathjax(answer)

                st.markdown("### Sources")
                if sources:
                    for src in sources:
                        st.markdown(
                            f"""
                        - **File Name:** {src.get('filename', '')}
                            - **Page Number:** {src.get('page number', '')}
                            - **Relevant Content:** {src.get('page content', '')}
                        """
                        )
                else:
                    st.markdown("No sources found.")
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
