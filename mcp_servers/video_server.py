from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("VideoSalesLetterServer")

@dataclass
class VideoScript:
    script_text: str

@mcp.tool()
def create_video_script(product_name: str, target_audience: str) -> VideoScript:
    """Creates a compelling video sales letter (VSL) script for a product."""
    script = (
        f"**(Opening Scene: Upbeat music, engaging visuals)**\n\n"
        f"**Host:** Are you a {target_audience} tired of common problems? Introducing **{product_name}**!\n\n"
        f"**(Scene 2: Problem showcase)**\n**Host:** {product_name} solves these issues by providing a unique solution...\n\n"
        f"**(Closing Scene: Call to action)**\n**Host:** Don't wait! Click the link below to get your {product_name} today!"
    )
    return VideoScript(script_text=script)