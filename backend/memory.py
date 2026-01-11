from typing import List, Dict

#Initializing memory
def init_memory(session_state):
    if "messages" not in session_state:
        session_state.messages = []

#Adding and retrieving messages
def add_message(session_state, role: str, content: str):
    session_state.messages.append({
        "role": role,
        "content": content
    })

#Retrieving full chat history
def get_history(session_state) -> List[Dict[str, str]]:
    return session_state.messages

# Clearing chat history
def clear_memory(session_state):
    session_state.messages = []
