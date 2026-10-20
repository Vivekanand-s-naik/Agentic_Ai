
import streamlit as st

st.title("🧠☠️ Deepagents Chatbot")

st.write("Planning . Virtual file system . Context engineering (AGENTS.md + memory) . Skills . Subagents (incl. structured output) . Swappable backends . Thread memory via checkpointer")

st.sidebar.header("Agent COnfigurations")

model = st.sidebar.selectbox(
    "model",
    ["groq:Openai/gpt-oss-20b", "", ""]
)


name = st.text_input("Enter your name")

if st.button("Submit"):
    st.success(f"Hello, {name}!")
