# server.py
import os
import json
import uvicorn
import traceback
import asyncio
import shutil
from contextlib import asynccontextmanager
from typing import List, Union, Literal, Optional
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from pydantic.v1 import BaseModel as LangChainBaseModel, Field
from langchain_core.tools import tool
from dotenv import load_dotenv


# --- Logic Imports ---
from mcp_servers.freelance_server import generate_project_proposal, ProjectProposal
from mcp_servers.video_server import create_video_from_script, VideoResult
from mcp_servers.support_server import get_support_answer, SupportResponse
from mcp_servers.virtual_employee_server import schedule_meeting, MeetingConfirmation
from mcp_servers.summarizer_server import analyze_and_summarize_transcript, ContentSummary
from mcp_servers.video_processing import extract_text_from_video
from mcp_servers.crm_server import draft_follow_up_email, EmailDraft, add_customer_interaction, CrmConfirmation
from mcp_servers.forecasting_server import (
    line_chart_forecast as forecast_line_logic,
    bar_chart_forecast as forecast_bar_logic,
    pie_chart_visualizer as visualize_pie_logic,
    forecast_and_generate_pie_charts as forecast_pie_logic,
    ForecastResult, PieSlice, ComparativePieChartResult
)
from mcp_servers.inbox_server import fetch_recent_emails
from mcp_servers.onboarding_server import generate_onboarding_checklist, OnboardingChecklist
from mcp_servers.flowchart_server import create_flowchart, FlowchartResult

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class ConnectionManager:
    def __init__(self): self.active_connections: dict[str, WebSocket] = {}
    async def connect(self, websocket: WebSocket, client_id: str): await websocket.accept(); self.active_connections[client_id] = websocket
    def disconnect(self, client_id: str):
        if client_id in self.active_connections: del self.active_connections[client_id]
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections: await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()
llm_with_tools: ChatOpenAI | None = None
llm_general: ChatOpenAI | None = None

def model_to_dict(model_instance):
    """
    A robust compatibility helper to convert any Pydantic model to a dictionary.
    It checks for the modern '.model_dump()' method (Pydantic v2) and falls back
    to the older '.dict()' method (Pydantic v1) if needed.
    """
    if hasattr(model_instance, 'model_dump'):
        return model_instance.model_dump()
    elif hasattr(model_instance, 'dict'):
        return model_instance.dict()
    else:
        raise TypeError(f"Object of type {type(model_instance).__name__} is not a serializable Pydantic model.")

@tool
def create_chart(
    data_name: str,
    chart_type: Literal["line", "bar", "pie"],
    data: Union[List[PieSlice], List[float]],
    is_forecast: bool = False,
    forecast_periods: int = 4
) -> Union[ForecastResult, ComparativePieChartResult]:
    """
    A unified tool to create charts. Handles line, bar, and pie charts,
    and can perform forecasting if requested.

    Args:
        data_name: The title of the chart (e.g., 'Quarterly Revenue').
        chart_type: The type of chart to create. Must be 'line', 'bar', or 'pie'.
        data: The data for the chart. This can be a list of numbers (e.g., [100, 200, 150])
              OR a list of labeled slices for a pie chart (e.g., [PieSlice(label='Sales', value=50)]).
        is_forecast: Set to True ONLY if the user explicitly asks to 'forecast', 'predict', or 'project' future data.
                     Defaults to False if the user just wants to visualize existing data.
        forecast_periods: The number of future periods to forecast.
    """
    if is_forecast:
        if not all(isinstance(x, (int, float)) for x in data):
            raise ValueError("Forecasting requires a list of numbers.")
        
        if chart_type == 'line':
            return forecast_line_logic(historical_data=data, data_name=data_name, forecast_periods=forecast_periods)
        elif chart_type == 'bar':
            return forecast_bar_logic(historical_data=data, data_name=data_name, forecast_periods=forecast_periods)
        elif chart_type == 'pie':
            return forecast_pie_logic(historical_data=data, data_name=data_name, forecast_periods=forecast_periods)
    else:
        if chart_type == 'pie':
            return visualize_pie_logic(data_name=data_name, pie_data=data)
        else:
            return ForecastResult(
                data_name=data_name, chart_type=chart_type, labels=[f"P{i+1}" for i in range(len(data))],
                historical_data=data, forecast_data=[]
            )

@tool
def crm_follow_up_tool(customer_email: str) -> EmailDraft:
    """Use this tool to draft a personalized follow-up email to a known customer based on their interaction history."""
    return draft_follow_up_email(customer_email=customer_email)

@tool
def video_creator_tool(product_name: str, target_audience: str, key_benefit: str) -> VideoResult:
    """Generates a structured video script based on product details and then creates a full video from it."""
    script_prompt = f"""
    You are a professional video scriptwriter. Your task is to generate a script for a short marketing video.
    The output MUST be in the following exact format, with no extra text or explanations.

    ### Audio Script
    [Sentence 1 for voiceover]
    [Sentence 2 for voiceover]
    [Sentence 3 for voiceover, which is a call to action]

    ### Visual Prompts
    1. [A visual description for Sentence 1]
    2. [A visual description for Sentence 2]
    3. [A visual description for the call to action sentence]

    **Video Details:**
    - Product Name: {product_name}
    - Target Audience: {target_audience}
    - Key Benefit to Highlight: {key_benefit}
    """
    script_response = llm_general.invoke(script_prompt)
    script = script_response.content.strip()
    return create_video_from_script(product_name=product_name, script=script)

@tool
def flowchart_agent_tool(concept_description: str) -> FlowchartResult:
    """Use this to create a Mermaid.js flowchart diagram that illustrates a process, workflow, or concept described by the user."""
    return create_flowchart(concept_description=concept_description)

@tool
def freelance_proposal_tool(client_name: str, project_description: str) -> ProjectProposal:
    """Generates a professional project proposal for a client based on a project description."""
    return generate_project_proposal(client_name=client_name, project_description=project_description)

@tool
def content_summarizer_tool(transcript_text: str) -> ContentSummary:
    """Analyzes a transcript from a meeting or video, summarizing key points, identifying action items, and determining sentiment."""
    return analyze_and_summarize_transcript(transcript_text=transcript_text)

@tool
def customer_support_tool(customer_query: str) -> SupportResponse:
    """Answers customer questions from a knowledge base."""
    return get_support_answer(customer_query=customer_query)

@tool
def virtual_employee_tool(topic: str, attendees: List[str], date_time: str) -> MeetingConfirmation:
    """Schedules a meeting."""
    return schedule_meeting(topic=topic, attendees=attendees, date_time=date_time)

@tool
def onboarding_bot_tool(client_name: str, service_type: str) -> OnboardingChecklist:
    """Creates an onboarding checklist for a new client."""
    return generate_onboarding_checklist(client_name=client_name, service_type=service_type)

@tool
def inbox_zero_tool(limit: int = 5) -> str:
    """
    Connects to an email inbox, fetches a specified number of recent emails,
    and prepares a detailed prompt for a secondary AI agent to categorize and summarize them.
    """
    emails = fetch_recent_emails(limit=limit)
    prompt_for_ai = """You are an intelligent email sorting assistant. Your task is to analyze a list of emails and categorize each one.
**Instructions:**
1.  Assign each email to one of the following categories: `📌 Important`, `💤 Low Priority`, or `🚫 Spam/Fraud`.
2.  Provide a 1-sentence summary for each email.
3.  Format the final output as clean Markdown tables, with a separate table for each category.

### 📌 Important
| From | Subject | Summary |
|:-----|:--------|:--------|

### 💤 Low Priority
| From | Subject | Summary |
|:-----|:--------|:--------|

### 🚫 Spam/Fraud
| From | Subject | Summary |
|:-----|:--------|:--------|
---
Here are the emails to classify:
"""
    for i, e in enumerate(emails, start=1):
        prompt_for_ai += (
            f"\n---\n"
            f"**Email {i}**:\n"
            f"- **From**: {e.sender}\n"
            f"- **Subject**: {e.subject}\n"
            f"- **Body Preview**: {e.body[:400]}...\n"
        )
    return prompt_for_ai

ALL_TOOLS = [
    create_chart, crm_follow_up_tool, video_creator_tool, flowchart_agent_tool,
    freelance_proposal_tool, content_summarizer_tool, customer_support_tool,
    virtual_employee_tool, inbox_zero_tool, onboarding_bot_tool,
]

TOOL_NAME_TO_CONTENT_TYPE = {
    "create_chart": "chart",
    "crm_follow_up_tool": "email",
    "video_creator_tool": "video",
    "flowchart_agent_tool": "mermaid",
    "content_summarizer_tool": "summary",
    "inbox_zero_tool": "inbox_analysis",
}

app = FastAPI()

origins = ["http://localhost", "http://localhost:3000", "http://127.0.0.1", "http://127.0.0.1:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    global llm_with_tools, llm_general
    llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY, model="llama3-8b-8192", temperature=0.1)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    llm_general = llm
    print("✅ LLMs initialized successfully.")

@app.post("/upload_and_summarize/{client_id}")
async def upload_and_summarize(client_id: str, file: UploadFile = File(...)):
    response_payload = {}
    file_path = ""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        await manager.send_personal_message(json.dumps({"content_type": "text", "payload": {"content": f"File '{file.filename}' received. Starting transcription..."}}), client_id)
        
        transcript_text = await asyncio.to_thread(extract_text_from_video, file_path)
        
        if "Transcription failed" in transcript_text or not transcript_text.strip():
             raise Exception(transcript_text or "The video appears to contain no speech.")
             
        tool_output = content_summarizer_tool.func(transcript_text=transcript_text)
        payload_data = model_to_dict(tool_output)
        final_payload = {"intro_text": f"Here is the summary for '{file.filename}':", **payload_data}
        response_payload = {"content_type": "summary", "payload": final_payload}

        await manager.send_personal_message(json.dumps(response_payload), client_id)
        
        return {"status": "success", "detail": "File processed and summary sent via WebSocket."}

    except Exception as e:
        print(traceback.format_exc())
        error_message = f"I encountered an error processing your file: {str(e)}"
        response_payload = {"content_type": "text", "payload": {"content": f"**Error:** {error_message}"}}
        await manager.send_personal_message(json.dumps(response_payload), client_id)
        
        return {"status": "error", "detail": str(e)}
        
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            raw_message = await websocket.receive_text()
            if not raw_message: continue
            message_data = json.loads(raw_message)
            user_message = message_data.get("content")
            response_payload = {}
            try:
                if not llm_with_tools or not llm_general: raise Exception("AI services are not available.")
                
                ai_response = await llm_with_tools.ainvoke(user_message)
                
                if ai_response.tool_calls:
                    tool_call = ai_response.tool_calls[0]
                    tool_name, tool_args = tool_call['name'], tool_call['args']
                    
                    print(f"--- AI ROUTER --- \nTool: {tool_name}\nArgs: {tool_args}\n---------------")
                    
                    target_tool = next((t for t in ALL_TOOLS if t.name == tool_name), None)
                    if not target_tool: raise Exception(f"LLM tried to call an unknown tool: {tool_name}")
                        
                    tool_output = await asyncio.to_thread(target_tool.func, **tool_args)
                    
                    if tool_name == "inbox_zero_tool":
                        print("--- AI AGENT --- \nStep 2: Generating email analysis report...\n---------------")
                        final_report = await llm_general.ainvoke(tool_output)
                        response_payload = {"content_type": "inbox_analysis", "payload": {"content": final_report.content}}
                    else:
                        payload_data = model_to_dict(tool_output)
                        content_type = TOOL_NAME_TO_CONTENT_TYPE.get(tool_name, "text")

                        if content_type == "text":
                            title = tool_name.replace('_tool', '').replace('_', ' ').title()
                            text_content = f"**{title}**\n\n"
                            for key, value in payload_data.items():
                                text_content += f"**{key.replace('_', ' ').capitalize()}:**\n{value}\n\n"
                            response_payload = {"content_type": "text", "payload": {"content": text_content.strip()}}
                        else:
                            final_payload = {"intro_text": f"Here is the '{payload_data.get('data_name')}' you requested:", **payload_data}
                            response_payload = {"content_type": content_type, "payload": final_payload}
                else:
                    print("--- AI ROUTER --- \nMode: General Conversation\n---------------")
                    final_response = await llm_general.ainvoke(user_message)
                    response_payload = {"content_type": "text", "payload": {"content": final_response.content}}

            except Exception as e:
                print(traceback.format_exc())
                response_payload = {"content_type": "text", "payload": {"content": f"**Error:** I encountered an error: {str(e)}"}}
            
            await manager.send_personal_message(json.dumps(response_payload), client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Client '{client_id}' disconnected.")
    except Exception as e:
        print(f"An error occurred for client '{client_id}': {e}")
        traceback.print_exc()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)