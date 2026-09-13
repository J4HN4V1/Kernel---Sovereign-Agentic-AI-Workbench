"""
Agent API routes.

Provides visibility into the agents participating in the
agentic workflow.
"""

from typing import Any

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


# ======================================================================
# AGENT REGISTRY
# ======================================================================

AGENTS: dict[str, dict[str, Any]] = {
    "planner": {
        "name": "Planner Agent",
        "type": "planning",
        "description": (
            "Breaks a complex user request into an executable "
            "multi-agent plan."
        ),
        "status": "available",
    },
    "document": {
        "name": "Document Agent",
        "type": "document_analysis",
        "description": (
            "Extracts and analyzes information from enterprise "
            "documents."
        ),
        "status": "available",
    },
    "vision": {
        "name": "Vision Agent",
        "type": "vision_analysis",
        "description": (
            "Analyzes images, diagrams and other visual inputs."
        ),
        "status": "available",
    },
    "reasoning": {
        "name": "Reasoning Agent",
        "type": "reasoning",
        "description": (
            "Performs local reasoning and determines whether "
            "additional capabilities are required."
        ),
        "status": "available",
    },
    "privacy": {
        "name": "Privacy Agent",
        "type": "security",
        "description": (
            "Checks sensitive information and determines whether "
            "external processing is permitted."
        ),
        "status": "available",
    },
}


# ======================================================================
# LIST AGENTS
# ======================================================================


@router.get("")
async def list_agents() -> dict[str, Any]:
    """
    Return all agents participating in the workflow.
    """

    agents = list(AGENTS.values())

    return {
        "count": len(agents),
        "agents": agents,
    }


# ======================================================================
# GET AGENT
# ======================================================================


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
) -> dict[str, Any]:
    """
    Return information about a specific agent.
    """

    agent = AGENTS.get(
        agent_id.lower()
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Agent '{agent_id}' was not found."
            ),
        )

    return {
        "agent_id": agent_id.lower(),
        **agent,
    }


# ======================================================================
# WORKFLOW
# ======================================================================


@router.get("/workflow/overview")
async def workflow_overview() -> dict[str, Any]:
    """
    Return the high-level agent execution flow.
    """

    return {
        "workflow": [
            "planner",
            "document",
            "vision",
            "reasoning",
            "privacy",
        ],
        "external_capability": {
            "enabled": True,
            "payment_protocol": "x402",
            "blockchain": "Algorand",
        },
    }