# =================================================================
# FINAL, DEPLOYMENT-READY, AND SOLVED server.py
# =================================================================
import os
import json
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found.")

# --- CONSOLIDATED MCP SERVER CONFIGURATION ---
# We now only start ONE background process, which saves memory on Render
MCP_SERVER_CONFIG = {
    "mcpServers": {
        "AllToolsServer": {
            "command": "mcp",
            "args": ["run", "./mcp_servers/all_tools_server.py"]
        }
    }
}

class ConnectionManager:
    # ... (no changes here)
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

# --- Global Objects ---
manager = ConnectionManager()
agent: MCPAgent | None = None  # The agent will be created on startup

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This function now correctly initializes the agent ONCE when the server starts
    global agent
    print("--- Server starting up... Initializing AI Agent now. ---")
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
            system_prompt="You are a helpful AI assistant..." # your full prompt
        )
        # We need to explicitly initialize the agent to connect to the tool servers
        await agent.initialize() 
        print("✅ Agent and consolidated tool server initialized successfully.")
    except Exception as e:
        print(f"❌ FATAL: Agent initialization failed: {e}")
        agent = None 
    yield
    print("--- Server shutting down. ---")

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    # The agent is already initialized, so we just check if it's ready
    if agent:
        welcome_payload = json.dumps({"type": "message", "data": "Connected to Vishesh Agent."})
        await manager.send_personal_message(welcome_payload, client_id)
    else:
        error_payload = json.dumps({"type": "error", "data": "Agent is not available, please check server logs."})
        await manager.send_personal_message(error_payload, client_id)
        return

    try:
        while True:
            user_message = await websocket.receive_text()
            if agent:
                agent_response = await agent.run(user_message)
                response_payload = json.dumps({"type": "response", "data": agent_response})
                await manager.send_personal_message(response_payload, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)