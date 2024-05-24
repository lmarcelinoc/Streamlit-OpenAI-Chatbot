import streamlit as st
import os
from dotenv import load_dotenv
from msal_streamlit_authentication import msal_authentication
from helpers.llm_helper import chat, stream_parser
from config import Config

# Set page configuration
st.set_page_config(
    page_title="Streamlit OpenAI Chatbot",
    initial_sidebar_state="expanded"
)

# Load environment variables from .env file
load_dotenv()
client_id = os.getenv("CLIENT_ID")
tenant_id = os.getenv("TENANT_ID")
scope = os.getenv("SCOPE")
redirectUri = "http://localhost:4000"

# Azure authentication
value = msal_authentication(
    login_button_text="Click to Login",
    auth={
        "clientId": client_id,
        "authority": "https://login.microsoftonline.com/" + tenant_id,
        "redirectUri": redirectUri,
        "postLogoutRedirectUri": "/"
    },
    cache={
        "cacheLocation": "sessionStorage",
        "storeAuthStateInCookie": False
    },
    login_request={
        "scopes": [scope]
    },
    key=1
)

if value:
    st.session_state['user_name'] = value['account']['name']

    st.title("Streamlit OpenAI Chatbot")

    # sets up sidebar nav widgets
    with st.sidebar:   
        st.markdown("# Chat Options")
        model = st.selectbox('What model would you like to use?',('gpt-3.5-turbo', 'gpt-4'))
        temperature = st.number_input('Temperature', value=0.7, min_value=0.1, max_value=1.0, step=0.1,
                                                help="The temperature setting to be used when generating output from the model.")
        max_token_length = st.number_input('Max Token Length', value=1000, min_value=200, max_value=1000, step=100, 
                                                help="Maximum number of tokens to be used when generating output.")
        
        # Display chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_prompt := st.chat_input("What questions do you have about the document?"):
            with st.chat_message("user"):
                st.markdown(user_prompt)
            st.session_state.messages.append({"role": "user", "content": user_prompt})

            with st.spinner('Generating response...'):
                llm_response = chat(user_prompt, model=model, max_tokens=max_token_length, temp=temperature)
                stream_output = st.write_stream(stream_parser(llm_response))
                st.session_state.messages.append({"role": "assistant", "content": stream_output})

            last_response =  st.session_state.messages[-1]['content']
            if str(last_response) != str(stream_output):
                with st.chat_message("assistant"):
                    st.markdown(stream_output)
else:
    st.warning("You must log in to access the chatbot.")
