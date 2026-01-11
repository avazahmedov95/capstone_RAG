import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

#Create Support Ticket
def create_support_ticket(name: str, email: str, summary: str, description: str):

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    body = f"""
**User name:** {name}  
**User email:** {email}  

---

{description}
"""

    payload = {
        "title": summary,
        "body": body,
        "labels": ["support", "ai-generated"]
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 201:
        raise Exception(f"GitHub API error: {response.text}")

    return {
        "status": "success",
        "issue_url": response.json()["html_url"]
    }

"""
support_ticket_schema = {
    "name": "create_support_ticket",
    "description": "Create a support ticket when user asks for help or answer is not found.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "User full name"
            },
            "email": {
                "type": "string",
                "description": "User email address"
            },
            "summary": {
                "type": "string",
                "description": "Short issue title"
            },
            "description": {
                "type": "string",
                "description": "Detailed issue description"
            }
        },
        "required": ["name", "email", "summary", "description"]
    }
}
"""

#LIST TICKETS
def list_support_tickets(limit: int = 5):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    params = {
        "state": "open",
        "labels": "support",
        "per_page": limit
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return [
        {
            "id": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"]
        }
        for issue in response.json()
    ]


list_support_tickets_schema = {
    "name": "list_support_tickets",
    "description": "List recent open support tickets",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of tickets to return"
            }
        }
    }
}


#CLOSE TICKET
def close_support_ticket(issue_id: int):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_id}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    payload = {"state": "closed"}

    response = requests.patch(url, json=payload, headers=headers)
    response.raise_for_status()

    return {
        "status": "closed",
        "issue_id": issue_id
    }


close_support_ticket_schema = {
    "name": "close_support_ticket",
    "description": "Close an existing support ticket",
    "parameters": {
        "type": "object",
        "properties": {
            "issue_id": {
                "type": "integer",
                "description": "GitHub issue number"
            }
        },
        "required": ["issue_id"]
    }
}