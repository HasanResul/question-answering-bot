"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message
from app import QABot

# StreamLit UI.
st.set_page_config(page_title="QA BOT", page_icon=":robot:")
st.header("QA BOT")

if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []

# qa_bot is run once and cached not to running eveytime a question is asked
@st.cache_resource
def qa_bot_creator():
    return QABot()

# initiate a qa_bot instance
qa_bot = qa_bot_creator()

# get user input
user_input = st.text_input("You: ")

if user_input:
    # answer question
    output = qa_bot.query(user_input)

    st.session_state.past.append(user_input)
    st.session_state.generated.append(output)

if st.session_state["generated"]:

    for i in range(len(st.session_state["generated"]) - 1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")