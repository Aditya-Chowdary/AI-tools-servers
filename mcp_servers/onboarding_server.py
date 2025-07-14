from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"), model="llama3-8b-8192")

class OnboardingChecklist(BaseModel):
    checklist: str

def generate_onboarding_checklist(client_name: str, service_type: str) -> OnboardingChecklist:
    """Creates a detailed onboarding checklist..."""
    prompt = f"You are a project manager... Create a detailed onboarding checklist for **Client:** {client_name} for our **Service:** {service_type}..."
    response = llm.invoke(prompt)
    checklist = f"**Onboarding Checklist for {client_name} ({service_type} Service)**\n\n{response.content}"
    return OnboardingChecklist(checklist=checklist)