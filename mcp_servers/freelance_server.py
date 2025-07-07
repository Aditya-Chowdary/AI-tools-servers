from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("FreelanceMarketplaceServer")

@dataclass
class ProjectProposal:
    proposal_text: str

@mcp.tool()
def generate_project_proposal(client_name: str, project_description: str) -> ProjectProposal:
    """Generates a professional project proposal for a client based on a project description."""
    proposal = (
        f"**Project Proposal for {client_name}**\n\n"
        f"**1. Project Overview**\nThis project aims to address the following: {project_description}\n\n"
        f"**2. Scope of Work**\n- Initial consultation and requirement gathering.\n- Development and implementation.\n- Testing and quality assurance.\n- Final delivery and handover.\n\n"
        f"**3. Next Steps**\nPlease review this proposal. We look forward to partnering with you."
    )
    return ProjectProposal(proposal_text=proposal)