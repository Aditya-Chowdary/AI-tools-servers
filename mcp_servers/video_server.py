# mcp_servers/video_server.py (Upgraded)
from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("VideoSalesLetterServer")

@dataclass
class VideoScript:
    title: str
    script_pas_framework: str # Problem-Agitate-Solve

@mcp.tool()
def create_video_script(product_name: str, primary_pain_point: str, target_audience: str) -> VideoScript:
    """Creates a compelling video sales letter (VSL) script using the Problem-Agitate-Solve framework."""
    
    script = (
        f"**SCENE START**\n\n"
        f"**(PROBLEM)**\n**NARRATOR (empathetic tone):** Are you a {target_audience} constantly struggling with {primary_pain_point}? It's frustrating, isn't it? You waste time and energy, and it holds you back from what you truly want to achieve.\n\n"
        f"**(AGITATE)**\n**NARRATOR:** Every day you ignore this problem, it gets worse. You miss opportunities, fall behind, and the stress just keeps building. Imagine a world where this wasn't an issue.\n\n"
        f"**(SOLVE)**\n**NARRATOR (upbeat shift):** Well, that world is here. Introducing **{product_name}**! The revolutionary new tool designed specifically to eliminate {primary_pain_point} forever. With our patented technology, you can get back to focusing on what matters. Don't wait. Click the link below and change your life today!\n\n"
        f"**SCENE END**"
    )
    return VideoScript(
        title=f"VSL Script for {product_name}",
        script_pas_framework=script
    )