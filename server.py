
import os
import json
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_openai import ChatOpenAI
import mcp_use
from mcp_use import MCPAgent, MCPClient
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY") # Don't forget this for the news tool

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

mcp_use.set_debug(True)
system_prompt = (
    "You are a helpful AI assistant named Vishesh. Use your available tools to answer user questions and complete tasks. "
    "Be concise, professional, and friendly. If a user's request is ambiguous or missing information needed for a tool, "
    "you MUST ask clarifying questions to get the required parameters. Do not try to guess."
)

# --- MCP SERVER CONFIGURATION (Corrected for Deployment) ---
# We list the server files. The system will find the 'mcp' command in its PATH.
SERVER_FILES = [
    "freelance_server.py", "video_server.py", "support_server.py",
    "virtual_employee_server.py", "summarizer_server.py", "crm_server.py",
    "forecasting_server.py", "inbox_server.py", "onboarding_server.py",
]

MCP_SERVER_CONFIG = {
    "mcpServers": {
        os.path.splitext(filename)[0]: { 
            "command": "mcp", 
            "args": ["run", f"./mcp_servers/{filename}"]
        } for filename in SERVER_FILES
    }
}

# --- All other code remains the same ---
class ConnectionManager:
    # ... (no changes needed here)
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client #{client_id} connected.")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()
agent: MCPAgent | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    print("--- Automatic Startup: Initializing Agent and starting MCP servers... ---")
    try:
        llm = ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY,
            model="llama3-70b-8192",
        )
        mcp_client = MCPClient(config=MCP_SERVER_CONFIG)
        agent = MCPAgent(
            llm=llm,
            client=mcp_client,
            max_steps=10,
            system_prompt=system_prompt
        )
        print("✅ Agent and all tool servers initialized successfully.")
    except Exception as e:
        print(f"❌ FATAL: Agent initialization failed: {e}")
        agent = None 
    yield
    print("Server is shutting down.")

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # ... (no changes needed here)
    await manager.connect(websocket, client_id)
    welcome_payload = json.dumps({"type": "message", "data": "Connected to Vishesh Agent."})
    await manager.send_personal_message(welcome_payload, client_id)
    try:
        while True:
            user_message = await websocket.receive_text()
            if agent:
                agent_response = await agent.run(user_message)
                response_payload = json.dumps({"type": "response", "data": agent_response})
                await manager.send_personal_message(response_payload, client_id)
            else:
                error_payload = json.dumps({"type": "error", "data": "Agent not available."})
                await manager.send_personal_message(error_payload, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)