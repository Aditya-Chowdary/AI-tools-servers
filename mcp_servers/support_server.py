from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("CustomerSupportServer")

@dataclass
class SupportResponse:
    answer: str

@mcp.tool()
def get_support_answer(customer_query: str) -> SupportResponse:
    """Provides an automated answer to a common customer support query."""
    query = customer_query.lower()
    if "reset password" in query:
        answer = "To reset your password, please go to the 'Account' page and click 'Forgot Password'."
    elif "shipping" in query:
        answer = "Standard shipping usually takes 3-5 business days. You can track your order via the link in your confirmation email."
    else:
        answer = "Thank you for your query. A support agent will get back to you shortly."
    return SupportResponse(answer=answer)