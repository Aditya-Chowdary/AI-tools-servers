from pydantic import BaseModel, Field
import datetime, re, os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"), model="llama3-8b-8192")

CRM_DATA = {
    "jane.doe@example.com": {
        "name": "Jane Doe", 
        "interactions": [
            {"date": "2023-10-15", "topic": "Initial inquiry about Enterprise Plan"}, 
            {"date": "2023-10-25", "topic": "Follow-up call regarding data security features"}
        ]
    }
}

class EmailDraft(BaseModel):
    recipient: str
    subject: str
    body: str

class CrmConfirmation(BaseModel):
    status: str
    customer_email: str
    details: str

def add_customer_interaction(customer_email: str, topic: str) -> CrmConfirmation:
    """Adds a new interaction to a customer's record in the CRM."""
    today_str = datetime.date.today().isoformat()
    if customer_email not in CRM_DATA:
        name = " ".join(word.capitalize() for word in customer_email.split('@')[0].split('.'))
        CRM_DATA[customer_email] = {"name": name, "interactions": []}
    CRM_DATA[customer_email]["interactions"].append({"date": today_str, "topic": topic})
    return CrmConfirmation(status="Success", customer_email=customer_email, details=f"Logged new interaction: '{topic}' on {today_str}.")

def draft_follow_up_email(customer_email: str) -> EmailDraft:
    """Drafts a personalized follow-up email based on the customer's interaction history."""
    if customer_email not in CRM_DATA:
        raise ValueError(f"Customer with email {customer_email} not found in CRM.")
    
    customer_info = CRM_DATA[customer_email]
    customer_name = customer_info["name"]
    interaction_history = "\n".join([f"- On {item['date']}, discussed: {item['topic']}" for item in customer_info['interactions']])
    last_topic = customer_info["interactions"][-1]["topic"] if customer_info["interactions"] else "our recent conversation"

    prompt = f"You are a sales assistant... [Full prompt here]"
    response = llm.invoke(prompt)
    email_content = response.content

    subject_match = re.search(r"Subject: (.*)", email_content)
    body_match = re.search(r"Body:\n(.*)", email_content, re.DOTALL)

    subject = subject_match.group(1).strip() if subject_match else f"Following up on {last_topic}"
    body = body_match.group(1).strip() if body_match else email_content

    return EmailDraft(recipient=customer_email, subject=subject, body=body)