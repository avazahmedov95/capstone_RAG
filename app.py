import streamlit as st

from backend.rag import answer_question, create_ticket_from_form
from backend.config import COMPANY_NAME, SUPPORT_EMAIL, SUPPORT_PHONE


st.set_page_config(page_title="Support Chat", layout="centered")

st.title(f"{COMPANY_NAME} Support Assistant")
st.caption(f"{SUPPORT_EMAIL} | {SUPPORT_PHONE}")


#Session state initialization

if "messages" not in st.session_state:
    st.session_state.messages = []

if "needs_confirmation" not in st.session_state:
    st.session_state.needs_confirmation = False

if "show_ticket_form" not in st.session_state:
    st.session_state.show_ticket_form = False

if "ticket_created" not in st.session_state:
    st.session_state.ticket_created = False

#Chat history display

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


#User input

user_input = st.chat_input("Ask your question")

if user_input:
    #Saving user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    #Showing user message
    with st.chat_message("user"):
        st.markdown(user_input)

    #Calling RAG to get answer
    with st.spinner("Thinking..."):
        result = answer_question(
            user_question=user_input,
            chat_history=st.session_state.messages
        )

    #Saving assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"]
    })

    #Updating confirmation state
    st.session_state.needs_confirmation = result.get("needs_confirmation", False)
    st.session_state.show_ticket_form = False

    st.rerun()

# Confirmation prompt

if st.session_state.needs_confirmation:
    st.warning("Would you like to create a support ticket?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Yes"):
            st.session_state.show_ticket_form = True
            st.session_state.needs_confirmation = False

    with col2:
        if st.button("No"):
            st.session_state.needs_confirmation = False
            st.info("Okay, no ticket was created.")


# Ticket creation form

if st.session_state.show_ticket_form and not st.session_state.ticket_created:
    st.subheader("Create support ticket")

    with st.form("ticket_form"):
        name = st.text_input("Your name")
        email = st.text_input("Your email")
        summary = st.text_input("Issue summary")
        description = st.text_area("Issue description")

        submitted = st.form_submit_button("Submit ticket")

        if submitted:
            result = create_ticket_from_form(
                name=name,
                email=email,
                summary=summary,
                description=description
            )

            st.session_state.ticket_created = True
            st.session_state.show_ticket_form = False

            st.success("✅ Support ticket created")
            st.markdown(f"🔗 [View ticket]({result['ticket_url']})")



