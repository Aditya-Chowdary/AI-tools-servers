# =================================================================
# FINAL "ALL-IN-ONE" server.py
# (Launches all tool servers automatically)
# =================================================================
import os
import json
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_openai import ChatOpenAI
import mcp_use
from mcp_use import MCPAgent, MCPClient
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

mcp_use.set_debug(True)
system_prompt = "You are a helpful AI assistant. Use your available tools to answer user questions and complete tasks. Be concise and professional."

# --- MCP SERVER CONFIGURATION (The "Automatic Startup" block) ---
# We use the absolute path to the mcp command inside the virtual environment
MCP_COMMAND = "/Users/adi/AI-tools-servers/.venv/bin/mcp"
SERVER_FILES = [
    "freelance_server.py", "video_server.py", "support_server.py",
    "virtual_employee_server.py", "summarizer_server.py", "crm_server.py",
    "forecasting_server.py", "inbox_server.py", "onboarding_server.py"
]

MCP_SERVER_CONFIG = {
    "mcpServers": {
        # Dynamically create the config for each server file
        os.path.splitext(filename)[0]: { # e.g., "freelance_server"
            "command": MCP_COMMAND,
            "args": ["run", f"./mcp_servers/{filename}"]
        } for filename in SERVER_FILES
    }
}


# --- CONNECTION MANAGER ---
class ConnectionManager:
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

# --- GLOBAL OBJECTS ---
manager = ConnectionManager()
agent: MCPAgent | None = None

# --- LIFESPAN FUNCTION FOR AUTOMATIC STARTUP ---
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
        
        # This will now use the config to launch all 9 servers in the background
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

# --- FASTAPI APPLICATION ---
app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
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

# --- TO RUN THE SERVER ---
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)