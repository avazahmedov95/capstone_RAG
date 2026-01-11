import json
from typing import List, Dict, Any
from pathlib import Path

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage

from backend.ticketing import create_support_ticket, list_support_tickets, close_support_ticket, list_support_tickets_schema, close_support_ticket_schema
from ingestion.build_index import build_faiss
from ingestion.ingest import extract_pages, chunk_pages

# Configurations
BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "vectorstore" / "faiss_index"
DATA_DIR = BASE_DIR / "data"

EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4o-mini"
TEMPERATURE = 0
TOP_K = 5


SYSTEM_PROMPT = """
You are a customer support assistant for an automotive company.

You must strictly follow the rules below.

====================
SUPPORTED VEHICLES
====================
You can answer questions ONLY for the following vehicles:
- 2023 Toyota Corolla Cross
- 2023 Toyota Corolla Hybrid
- 2025 Toyota Corolla Hatchback

These vehicles are documented in:
- 2023-toyota-corolla-cross.pdf
- 2023-toyota-corolla-hybrid.pdf
- 2025-corolla-hatchback.pdf

====================
INTENT DETECTION
====================
Classify the user's request into ONE intent:

1. general
   - greetings, small talk, thanks, questions about you

2. support
   - questions asking for help or instructions
   - maintenance, usage, or troubleshooting questions
   - questions about supported vehicles

3. ticket_management
   - explicit requests to create, open, view, list, or close a support ticket
   - examples:
     - "create a ticket"
     - "open a support ticket"
     - "show my tickets"
     - "close ticket 12"

====================
TICKET MANAGEMENT
====================
If intent is "ticket_management":

1. If the user asks to view or list tickets:
   - Call the function: list_support_tickets

2. If the user asks to close or delete a ticket:
   - Call the function: close_support_ticket

3. If the user asks to create or open a ticket:
   - DO NOT create the ticket automatically.
   - Politely ask the user to provide the required details:
     - name
     - email
     - summary
     - description

Do NOT generate answers from documentation in this case.

====================
SUPPORT QUESTIONS
====================
If intent is "support":

1. Identify the vehicle model mentioned by the user.

2. If the vehicle is NOT supported:
   - Say that the information is not available for that vehicle.
   - Ask if the user wants to create a support ticket.

3. If the vehicle IS supported:
   - Search the provided documents.
   - If relevant information IS FOUND:
     - Answer using ONLY the documentation.
     - Cite the source as:
       (source: <file>, page <page>)
   - If relevant information is NOT FOUND:
     - Say that the information could not be found.
     - Ask if the user wants to create a support ticket.

====================
GENERAL QUESTIONS
====================
If intent is "general":
- Answer politely.
- Do NOT mention documentation.
- Do NOT mention support tickets.

====================
OUTPUT FORMAT
====================
If no function is called, return ONLY valid JSON:

{
  "intent": "general | support | ticket_management",
  "answer": "<final answer text>",
  "needs_confirmation": true | false
}
"""



#RAG Logic
def load_vectorstore():
    index_path = Path(INDEX_DIR)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    if not index_path.exists():
        print("FAISS index not found. Building index...")

        all_chunks = []

        for pdf in Path(DATA_DIR).glob("*.pdf"):
            pages = extract_pages(str(pdf))
            chunks = chunk_pages(pages)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise RuntimeError("No chunks extracted from PDFs")

        build_faiss(
            chunks=all_chunks,
            embeddings=embeddings,
            save_path=INDEX_DIR
        )

        if not index_path.exists():
            raise RuntimeError("FAISS index build failed")

        print("FAISS index built successfully")
    return FAISS.load_local(
        INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

#Context Builder
def build_context(docs):
    blocks = []
    for d in docs:
        blocks.append(
            f"[File: {d.metadata['file']}, Page: {d.metadata['page']}]\n{d.page_content}"
        )
    return "\n\n".join(blocks)

#Answering Function
def answer_question(
    user_question: str,
    chat_history: List[Dict[str, str]]
) -> Dict[str, Any]:

    vectorstore = load_vectorstore()
    docs = vectorstore.similarity_search(user_question, k=TOP_K)

    llm = ChatOpenAI(model=LLM_MODEL, temperature=TEMPERATURE)

    context = build_context(docs) if docs else "NO_DOCUMENTS_FOUND"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
User question:
{user_question}

Documents:
{context}
""")
    ]

    response = llm.invoke(
        messages,
        functions=[
            list_support_tickets_schema,
            close_support_ticket_schema
        ],
        function_call="auto"
    )

    function_call = response.additional_kwargs.get("function_call")

    if function_call:
        fn = function_call["name"]
        args = json.loads(function_call.get("arguments", "{}"))

        if fn == "list_support_tickets":
            tickets = list_support_tickets(**args)
            return {
                "intent": "ticket_management",
                "answer": format_tickets(tickets),
                "needs_confirmation": False
            }
        if fn == "close_support_ticket":
            result = close_support_ticket(**args)
            return {
                "intent": "ticket_management",
                "answer": f"Ticket #{result['issue_id']} has been closed.",
                "needs_confirmation": False
            }

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        return {
            "intent": "general",
            "answer": "Sorry, I had trouble understanding the request.",
            "needs_confirmation": False
        }

    return result

#Ticket Formatting
def format_tickets(tickets: list[dict]) -> str:
    if not tickets:
        return "There are no open support tickets."

    lines = ["Here are the open support tickets:"]

    for t in tickets:
        lines.append(
            f"- #{t['id']}: {t['title']} ({t['url']})"
        )

    return "\n".join(lines)

# Ticket Creation from Form
def create_ticket_from_form(name, email, summary, description):
    result = create_support_ticket(
        name=name,
        email=email,
        summary=summary,
        description=description
    )

    return {
        "ticket_created": True,
        "ticket_url": result["issue_url"]
    }
