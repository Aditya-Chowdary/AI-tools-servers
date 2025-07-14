# mcp_servers/flowchart_server.py
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()
llm = ChatOpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("GROQ_API_KEY"), model="llama3-8b-8192", temperature=0.0)

class FlowchartResult(BaseModel):
    title: str
    mermaid_code: str

def create_flowchart(concept_description: str) -> FlowchartResult:
    """
    Analyzes a natural language description and converts it into a visually appealing Mermaid.js flowchart.
    """
    prompt = f"""
    You are an expert at generating Mermaid.js flowchart code.
    Your task is to convert the user's request into a valid, visually appealing Mermaid.js `graph TD` definition.

    **RULES:**
    1.  **ONLY output the Mermaid.js code block.** Do NOT include ```mermaid wrappers or any explanations.
    2.  The flowchart must start with `graph TD;`.
    3.  **Use different shapes for clarity:**
        -   Start/End nodes: `id(Text)` - renders as a rounded rectangle.
        -   Process/Action nodes: `id[Text]` - renders as a sharp-cornered rectangle.
        -   Decision/Question nodes: `id{{Text?}}` - renders as a rhombus/diamond.
    4.  If the request is not a process, your ONLY output should be: `graph TD; A["I am unable to create a flowchart for this concept."];`

    **EXAMPLE:**
    User Request: "Show the process of making coffee."
    Your Output:
    graph TD;
        A(Start) --> B{{Have coffee beans?}};
        B -- Yes --> C[Grind beans];
        B -- No --> D[Buy beans];
        D --> C;
        C --> E[Brew coffee];
        E --> F[Serve coffee];
        F --> G(End);

    ---
    **User Request:**
    "{concept_description}"

    **Your Output:**
    """

    response = llm.invoke(prompt)
    mermaid_code = response.content.strip()

    # Fallback cleanup
    if "```mermaid" in mermaid_code:
        mermaid_code = re.search(r"```mermaid(.*)```", mermaid_code, re.DOTALL).group(1).strip()
    elif mermaid_code.startswith("```"):
         mermaid_code = mermaid_code.replace("```", "").strip()
    if not mermaid_code.lower().startswith(('graph', 'flowchart')):
        mermaid_code = "graph TD;\n" + mermaid_code

    title_text = concept_description
    if len(title_text) > 40:
        title_text = title_text[:37] + "..."
    
    return FlowchartResult(
        title=f"Flowchart for '{title_text}'", 
        mermaid_code=mermaid_code
    )