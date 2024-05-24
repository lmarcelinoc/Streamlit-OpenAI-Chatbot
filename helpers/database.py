import sqlite3
from contextlib import closing

def init_db():
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cursor.fetchone():
                print("Creating tables...")
                cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                    id INTEGER PRIMARY KEY,
                                    username TEXT UNIQUE,
                                    password TEXT)''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS chats (
                                    id INTEGER PRIMARY KEY,
                                    user_id INTEGER,
                                    chat_name TEXT,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    FOREIGN KEY(user_id) REFERENCES users(id))''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                                    id INTEGER PRIMARY KEY,
                                    chat_id INTEGER,
                                    role TEXT,
                                    content TEXT,
                                    FOREIGN KEY(chat_id) REFERENCES chats(id))''')
                conn.commit()
                print("Tables created successfully.")
            else:
                print("Tables already exist. Skipping creation.")

def add_user(username, password):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print(f"User {username} added to the database.")

def get_user(username):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            print(f"Fetched user: {user}")
            return user

def create_chat(user_id, chat_name):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("INSERT INTO chats (user_id, chat_name) VALUES (?, ?)", (user_id, chat_name))
        conn.commit()
        chat_id = cursor.lastrowid
        print(f"Chat {chat_name} created with ID {chat_id}.")
        return chat_id

def get_chats(user_id):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT id, chat_name FROM chats WHERE user_id = ?", (user_id,))
            chats = cursor.fetchall()
            print(f"Fetched chats for user {user_id}: {chats}")
            return chats

def add_message(chat_id, role, content):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
        conn.commit()
        print(f"Message added to chat {chat_id}: {role}, {content}")

def get_messages(chat_id):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT role, content FROM messages WHERE chat_id = ?", (chat_id,))
            messages = cursor.fetchall()
            print(f"Fetched messages for chat {chat_id}: {messages}")
            return messages

def delete_chat(chat_id):
    with closing(sqlite3.connect('chatbot.db')) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        print(f"Deleted chat {chat_id} and all associated messages.")
