import streamlit as st
import os
from dotenv import load_dotenv
from msal_streamlit_authentication import msal_authentication
from helpers.llm_helper import chat, stream_parser
from config import Config
from helpers.database import init_db, add_user, get_user, create_chat, get_chats, add_message, get_messages, delete_chat

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
redirectUri = os.getenv("HOST")

# Initialize the database
print("Initializing the database...")
init_db()

# Azure authentication
print("Starting Azure authentication...")
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
    print(f"Authenticated user: {value['account']['name']}")
    st.session_state['user_name'] = value['account']['name']
    user = get_user(st.session_state['user_name'])
    if not user:
        add_user(st.session_state['user_name'], "password")  # Example, no actual password management

    user_id = get_user(st.session_state['user_name'])[0]

    # Sidebar for chat options and logout
    with st.sidebar:
        st.markdown("# Chat Options")
        model = st.selectbox('What model would you like to use?', ('gpt-3.5-turbo', 'gpt-4'))
        temperature = st.number_input('Temperature', value=0.7, min_value=0.1, max_value=1.0, step=0.1,
                                      help="The temperature setting to be used when generating output from the model.")
        max_token_length = st.number_input('Max Token Length', value=1000, min_value=200, max_value=1000, step=100,
                                           help="Maximum number of tokens to be used when generating output.")

        st.markdown("---")
        if st.button('Logout'):
            st.session_state.clear()
            st.rerun()

        st.markdown("## Chats")
        if st.button("New Chat") or not st.session_state.get('current_chat_id'):
            chat_name = f"Chat {len(get_chats(user_id)) + 1}"
            new_chat_id = create_chat(user_id, chat_name)
            st.session_state['current_chat'] = chat_name
            st.session_state['current_chat_id'] = new_chat_id
            st.session_state.messages = []
            print(f"Created new chat: {chat_name}")

        chat_names = get_chats(user_id)
        if chat_names:
            chat_names_dict = {name: id for id, name in chat_names}
            selected_chat = st.selectbox("Select Chat", options=list(chat_names_dict.keys()))
            if selected_chat != st.session_state.get('current_chat'):
                st.session_state['current_chat'] = selected_chat
                st.session_state['current_chat_id'] = chat_names_dict[selected_chat]
                st.session_state.messages = [{"role": role, "content": content} for role, content in get_messages(st.session_state['current_chat_id'])]
                print(f"Selected chat: {selected_chat}")

            if st.button("Delete Current Chat"):
                delete_chat(st.session_state['current_chat_id'])
                st.session_state['current_chat'] = None
                st.session_state['current_chat_id'] = None
                st.session_state.messages = []
                print("Deleted current chat.")
                st.rerun()
        else:
            st.session_state['current_chat'] = None
            st.session_state['current_chat_id'] = None
            print("No chats available.")

    current_chat_id = st.session_state.get('current_chat_id')
    if current_chat_id:
        messages = get_messages(current_chat_id)
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": role, "content": content} for role, content in messages]
            print(f"Loaded messages for chat ID {current_chat_id}")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input for user prompts
        if user_prompt := st.chat_input("What questions do you have about the document?"):
            with st.chat_message("user"):
                st.markdown(user_prompt)
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            add_message(current_chat_id, "user", user_prompt)
            print(f"User message added: {user_prompt}")

            with st.spinner('Generating response...'):
                llm_response = chat(user_prompt, model=model, max_tokens=max_token_length, temp=temperature)
                stream_output = st.write_stream(stream_parser(llm_response))
                st.session_state.messages.append({"role": "assistant", "content": stream_output})
                add_message(current_chat_id, "assistant", stream_output)
                print(f"Assistant response added: {stream_output}")

            last_response = st.session_state.messages[-1]['content']
            if str(last_response) != str(stream_output):
                with st.chat_message("assistant"):
                    st.markdown(stream_output)
else:
    st.warning("You must log in to access the chatbot.")
