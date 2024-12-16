# %%
import os
import json
import requests
import datetime

import streamlit as st


from ollama import Client

OLLAMA_URL = os.environ.get('OLLAMA_URL')


client = Client(
  host=OLLAMA_URL
)


def st_ollama(model_name, user_question, chat_history_key):

    if chat_history_key not in st.session_state.keys():
        st.session_state[chat_history_key] = []

    print_chat_history_timeline(chat_history_key)

    # run the model
    if user_question:
        st.session_state[chat_history_key].append({"content": f"{user_question}", "role": "user"})
        with st.chat_message("question", avatar="🧑‍🚀"):
            st.write(user_question)

        messages = [dict(content=message["content"], role=message["role"]) for message in st.session_state[chat_history_key]]

        def llm_stream(response):
            response = client.chat(model_name, messages, stream=True)
            for chunk in response:
                yield chunk['message']['content']

        # streaming response
        with st.chat_message("response", avatar="🤖"):
            chat_box = st.empty()
            response_message = chat_box.write_stream(llm_stream(messages))

        st.session_state[chat_history_key].append({"content": f"{response_message}", "role": "assistant"})

        return response_message


def print_chat_history_timeline(chat_history_key):
    for message in st.session_state[chat_history_key]:
        role = message["role"]
        if role == "user":
            with st.chat_message("user", avatar="🧑‍🚀"): 
                question = message["content"]
                st.markdown(f"{question}", unsafe_allow_html=True)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"], unsafe_allow_html=True)


# -- helpers --




def save_conversation(llm_name, conversation_key):

    OUTPUT_DIR = "llm_conversations"
    OUTPUT_DIR = os.path.join(os.getcwd(), OUTPUT_DIR)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{OUTPUT_DIR}/{timestamp}_{llm_name.replace(':', '-')}"

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if st.session_state[conversation_key]:

        if st.sidebar.button("Save conversation"):
            with open(f"{filename}.json", "w") as f:
                json.dump(st.session_state[conversation_key], f, indent=4)
            st.success(f"Conversation saved to {filename}.json")


if __name__ == "__main__":

    st.set_page_config(layout="wide", page_title="Ollama Chat", page_icon="🦙")

    st.sidebar.title(f"Ollama Chat 🦙: {OLLAMA_URL}")
    llm_name = "phi3.5"

    conversation_key = f"model_{llm_name}"
    prompt = st.chat_input(f"Ask '{llm_name}' a question ...")

    st_ollama(llm_name, prompt, conversation_key)
    
    if st.session_state[conversation_key]:
        clear_conversation = st.sidebar.button("Clear chat")
        if clear_conversation:
            st.session_state[conversation_key] = []
            st.rerun()

    # save conversation to file
    save_conversation(llm_name, conversation_key)
