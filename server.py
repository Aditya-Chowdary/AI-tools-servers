
import os
import asyncio
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

# It's good practice to check if the key was found
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not found. Please set it in your .env file or system environment.")

mcp_use.set_debug(True)

system_prompt = (
    "Your role is to help users by completing tasks using your available task capabilities. "
    "and explain your capabilities using the information from the 'my_profile' task. "
    "Do not mention the word 'tool'; describe your functions as user tasks you can perform."
    """ You should act based on your available tools, and leverage them intelligently to complete user requests.

                            remember: 
                             - if use ask anything you capability then you should say based on you tools you should say your capability to your user.
                             - dont tell the user like 'tool' instead of tool you should say user task
                             - If the user does not provide required input, intelligently generate a clear, efficient, and professional default using available data—applying sensible assumptions (e.g., latest 10 results, standard filters)—to ensure relevance and minimal overload, then follow up with a helpful question to clarify or refine the request."""
)

MCP_SERVER_CONFIG = {
    "mcpServers": {
        "DummyToolDemo": {  # IMPORTANT: This name must match FastMCP("...") in your server file
            "command": "uv",  # Assumes 'uv' is in your system's PATH
            "args": [
                "run",
                "--with",
                "mcp[cli]",
                "mcp",
                "run",
                "./mcp servers/mcp_server1.py"  # Use the dynamic path to your server file
            ]
        }
    }
}

# --- Connection Manager (from your reference) ---
class ConnectionManager:
    def __init__(self):
        # We use a dictionary to map a client_id to its WebSocket connection
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client #{client_id} connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client #{client_id} disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

# --- Global Objects ---
manager = ConnectionManager()
agent: MCPAgent | None = None  # Initialize agent as None

# --- FastAPI Lifespan for Startup/Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on server startup
    global agent
    print("Initializing MCP Agent and LLM...")
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
        print("✅ Agent successfully initialized.")
    except Exception as e:
        print(f"❌ FATAL: Agent initialization failed: {e}")
        agent = None # Ensure agent is None if startup fails

    yield  # The application runs here

    # This code runs on server shutdown (optional)
    print("Server is shutting down.")


# --- FastAPI Application ---
app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    # Send a welcome message
    welcome_payload = json.dumps({"type": "message", "data": "Connected to Vishesh Agent."})
    await manager.send_personal_message(welcome_payload, client_id)

    try:
        while True:
            # Wait for a message from the client
            user_message = await websocket.receive_text()

            if agent:
                # Process the message with the agent
                agent_response = await agent.run(user_message)
                response_payload = json.dumps({"type": "response", "data": agent_response})
                await manager.send_personal_message(response_payload, client_id)
            else:
                # Handle the case where the agent failed to initialize
                error_payload = json.dumps({"type": "error", "data": "Agent is not available due to an initialization error. Please check server logs."})
                await manager.send_personal_message(error_payload, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        # Catch other potential errors during communication
        print(f"An error occurred with client #{client_id}: {e}")
        manager.disconnect(client_id)

# --- To run the server ---
if __name__ == "__main__":
    # Use 0.0.0.0 to make it accessible on your network
    # The default port for FastAPI/Uvicorn is 8000
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=8000, reload=True)
