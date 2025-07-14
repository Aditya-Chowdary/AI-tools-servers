from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"), model="llama3-8b-8192")

class ProjectProposal(BaseModel):
    proposal_text: str

def generate_project_proposal(client_name: str, project_description: str) -> ProjectProposal:
    """Generates a professional project proposal..."""
    prompt = f"You are a professional business consultant...\n**Client Name:** {client_name}\n**Project Description:** {project_description}\n..."
    response = llm.invoke(prompt)
    return ProjectProposal(proposal_text=response.content)