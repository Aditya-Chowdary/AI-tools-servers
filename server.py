# server.py
import os
import json
import uvicorn
import traceback
import asyncio
from contextlib import asynccontextmanager
from typing import List, Union
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from dotenv import load_dotenv

# --- All your tool imports remain the same ---
from mcp_servers.freelance_server import generate_project_proposal, ProjectProposal
from mcp_servers.video_server import create_video_from_script, VideoResult
from mcp_servers.support_server import get_support_answer, SupportResponse
from mcp_servers.virtual_employee_server import schedule_meeting, MeetingConfirmation
from mcp_servers.summarizer_server import analyze_and_summarize_transcript, ContentSummary
# --- NEW: Import the video processor ---
from mcp_servers.video_processing import extract_text_from_video
from mcp_servers.crm_server import draft_follow_up_email, EmailDraft, add_customer_interaction, CrmConfirmation
from mcp_servers.forecasting_server import forecast_data, ForecastResult
from mcp_servers.inbox_server import categorize_email, EmailCategory
from mcp_servers.onboarding_server import generate_onboarding_checklist, OnboardingChecklist
from mcp_servers.flowchart_server import create_flowchart, FlowchartResult

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- ConnectionManager remains the same ---
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

# --- All your @tool definitions remain the same ---
@tool
def financial_forecasting_tool(historical_data: List[Union[int, float]], data_name: str, forecast_periods: int = 4) -> ForecastResult:
    """Generates a realistic forecast using an ARIMA model. Use this for predicting future data points based on historical trends, like sales, revenue, or user signups."""
    return forecast_data(historical_data=historical_data, data_name=data_name, forecast_periods=forecast_periods)

@tool
def crm_follow_up_tool(customer_email: str) -> EmailDraft:
    """Drafts a personalized follow-up email to a customer based on their interaction history in the CRM."""
    return draft_follow_up_email(customer_email=customer_email)

@tool
def crm_logging_tool(customer_email: str, topic: str) -> CrmConfirmation:
    """Adds or logs a new interaction (like a call or meeting) with a customer in the CRM."""
    return add_customer_interaction(customer_email=customer_email, topic=topic)

@tool
def video_creator_tool(product_name: str, target_audience: str, key_benefit: str) -> VideoResult:
    """
    Creates a full marketing video with generated voiceover and slides.
    Use this for any request to "create a video".
    You MUST extract 'product_name', 'target_audience', and 'key_benefit'.
    """
    print("Video creator tool started. Step 1: Generating script...")
    
    # Step A: Generate the script using the general LLM
    script_prompt = f"""
    You are a scriptwriter. Your one and only task is to write a short video script based on the user's request.
    **CRITICAL RULE: Your output MUST ONLY contain the script lines and nothing else. Do not add any introductory text, headers, or conversational filler. Your output must be ONLY the script itself.**

    The script is for a product named '{product_name}' targeting '{target_audience}'.
    The main benefit to highlight is '{key_benefit}'.
    It must have 3 to 4 distinct sentences.
    Each sentence MUST be on a new line. Do not use bullet points.
    The final sentence must be a strong call to action.
    """
    
    script_response = llm_general.invoke(script_prompt)
    raw_script = script_response.content.strip()

    # --- FIXED: Clean up the script to remove any conversational filler from the LLM ---
    lines = raw_script.split('\n')
    first_real_line_index = 0
    for i, line in enumerate(lines):
        # Find the first line that doesn't contain common filler words and start from there
        if not any(word in line.lower() for word in ["here's", "here is", "sure", "script:", "certainly"]):
            first_real_line_index = i
            break
            
    script = '\n'.join(lines[first_real_line_index:]).strip()
    
    print(f"Cleaned script:\n---\n{script}\n---")
    print("Step 2: Calling local video creation function...")

    # Step B: Call the local Python function with the generated script
    return create_video_from_script(product_name=product_name, script=script)

@tool
def flowchart_agent_tool(concept_description: str) -> FlowchartResult:
    """
    Use this tool to generate a flowchart diagram for any process, workflow, or concept. 
    It is the best choice for visualizing steps or creating diagrams. 
    For example, if the user asks 'create a flowchart of the scientific method', 'visualize how rain is formed', or 'map out the customer support process', this tool must be used.
    """
    return create_flowchart(concept_description=concept_description)


@tool
def freelance_proposal_tool(client_name: str, project_description: str) -> ProjectProposal:
    """Generates a professional project proposal for a client based on a project description."""
    return generate_project_proposal(client_name=client_name, project_description=project_description)

@tool
def content_summarizer_tool(transcript_text: str) -> ContentSummary:
    """
    Analyzes and summarizes a provided block of text from a meeting or video transcript.
    It extracts key points, action items, and sentiment. Use this for any summarization request.
    If the user pastes a large block of text and asks "what is this?" or "summarize this", this is the tool to use.
    """
    print(f"Summarizing text of length: {len(transcript_text)}")
    return analyze_and_summarize_transcript(transcript_text=transcript_text)


@tool
def customer_support_tool(customer_query: str) -> SupportResponse:
    """Answers customer questions by searching a knowledge base. Use for queries about passwords, shipping, refunds, etc."""
    return get_support_answer(customer_query=customer_query)

@tool
def virtual_employee_tool(topic: str, attendees: List[str], date_time: str) -> MeetingConfirmation:
    """Schedules a meeting with specified attendees at a given date and time."""
    return schedule_meeting(topic=topic, attendees=attendees, date_time=date_time)

@tool
def inbox_zero_tool(subject: str, sender: str) -> EmailCategory:
    """Categorizes an email based on its subject and sender to determine its priority (Important, General, Promotions)."""
    return categorize_email(subject=subject, sender=sender)

@tool
def onboarding_bot_tool(client_name: str, service_type: str) -> OnboardingChecklist:
    """Creates a detailed onboarding checklist for a new client based on the service they signed up for."""
    return generate_onboarding_checklist(client_name=client_name, service_type=service_type)

ALL_TOOLS = [
    financial_forecasting_tool, crm_follow_up_tool, crm_logging_tool, video_creator_tool,
    flowchart_agent_tool, freelance_proposal_tool,content_summarizer_tool,
    customer_support_tool, virtual_employee_tool, inbox_zero_tool, onboarding_bot_tool,
]

# --- This mapping is crucial for sending the correct widget type to the frontend ---
TOOL_NAME_TO_CONTENT_TYPE = {
    "financial_forecasting_tool": "chart",
    "crm_follow_up_tool": "email",
    "video_creator_tool": "video",
    "flowchart_agent_tool": "mermaid",
  "content_summarizer_tool": "summary",
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
@app.on_event("startup")
async def startup_event():
    global llm_with_tools, llm_general
    base_llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY, model="llama3-8b-8192", temperature=0.1)
    llm_with_tools = base_llm.bind_tools(ALL_TOOLS)
    llm_general = base_llm
    print("✅ LLMs initialized successfully.")

    # --- NEW: Add a file upload endpoint ---
@app.post("/upload_and_summarize/{client_id}")
async def upload_and_summarize(client_id: str, file: UploadFile = File(...)):
    """
    Handles video file uploads. It saves the file, extracts text, summarizes it,
    and sends the result back to the specific client via WebSocket.
    """
    response_payload = {}
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # 1. Save the uploaded file to the temp directory
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Inform frontend that transcription is starting
        await manager.send_personal_message(
            json.dumps({"content_type": "text", "payload": {"content": f"File '{file.filename}' received. Starting transcription (this may take a few moments)..."}}),
            client_id
        )

        # 3. Extract text from video (this is a blocking IO operation)
        transcript_text = await asyncio.to_thread(extract_text_from_video, file_path)

        if "Transcription failed" in transcript_text or not transcript_text.strip():
             raise Exception(transcript_text or "The video appears to contain no speech.")

        # 4. Summarize the extracted text using the existing tool logic
        tool_output = content_summarizer_tool.func(transcript_text=transcript_text)
        payload_data = tool_output.model_dump()

        # 5. Package the response for the frontend widget
        final_payload = {"intro_text": f"Here is the summary for '{file.filename}':", **payload_data}
        response_payload = {"content_type": "summary", "payload": final_payload}

    except Exception as e:
        print(traceback.format_exc())
        error_message = f"I encountered an error processing your file: {str(e)}"
        response_payload = {"content_type": "text", "payload": {"content": f"**Error:** {error_message}"}}
        # Clean up failed file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)

    await manager.send_personal_message(json.dumps(response_payload), client_id)
    return {"status": "processing_complete"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            raw_message = await websocket.receive_text()
            if not raw_message: continue
            
            message_data = json.loads(raw_message)
            message_type = message_data.get("type")
            
            # --- FIX: The `run_agent` message type is now obsolete and has been removed. ---
            # All logic is now handled by the `text_message` AI router below.

            if message_type == "text_message":
                user_message = message_data.get("content")
                response_payload = {}
                
                try:
                    if not llm_with_tools or not llm_general:
                        raise Exception("AI services are not available.")

                    # Step 1: Let the AI router decide which tool to use, if any.
                    ai_response = await llm_with_tools.ainvoke(user_message)
                    
                    if ai_response.tool_calls:
                        tool_call = ai_response.tool_calls[0]
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        
                        target_tool = next((t for t in ALL_TOOLS if t.name == tool_name), None)
                        if not target_tool:
                            raise Exception(f"LLM tried to call an unknown tool: {tool_name}")
                        
                        # Step 2: Execute the chosen tool.
                        tool_output = await asyncio.to_thread(target_tool.func, **tool_args)
                        
                        payload_data = tool_output.model_dump() if hasattr(tool_output, 'model_dump') else {"content": str(tool_output)}
                        
                        # Step 3: Package the response for the frontend widget.
                        content_type = TOOL_NAME_TO_CONTENT_TYPE.get(tool_name, "text") # Default to text

                        final_payload = payload_data
                        # For certain widgets, we can add introductory text.
                        if content_type == "email": final_payload = {"intro_text": "I've drafted this email for you:", **payload_data}
                        elif content_type == "video": final_payload = {"intro_text": "Video script generation initiated:", **payload_data}
                        elif content_type == "video_summary": final_payload = {"intro_text": "Here is the summary of the video:", **payload_data}
                        elif content_type == "mermaid": final_payload = {"intro_text": "Here is the generated flowchart:", **payload_data}
                        elif content_type == "text": # For tools that return text, ensure it's in the right format.
                           final_payload = {"content": next(iter(payload_data.values()), str(payload_data))}

                        response_payload = {"content_type": content_type, "payload": final_payload}
                    
                    else:
                        # Step 4: If no tool was chosen, fall back to a general text response.
                        final_response = await llm_general.ainvoke(f"As a helpful AI assistant, provide a concise response to the following user query: {user_message}")
                        response_payload = {"content_type": "text", "payload": {"content": final_response.content}}

                except Exception as e:
                    print(traceback.format_exc())
                    error_message = f"I encountered an error processing your request: {str(e)}"
                    response_payload = {"content_type": "text", "payload": {"content": f"**Error:** {error_message}"}}

                # --- FIX: Simplified the final send message call ---
                await manager.send_personal_message(json.dumps(response_payload), client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Client '{client_id}' disconnected.")
    except Exception as e:
        print(f"An error occurred in websocket for client '{client_id}': {e}")
        traceback.print_exc()
        manager.disconnect(client_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)