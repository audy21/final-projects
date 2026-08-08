from fastapi import APIRouter, Depends
from typing import Literal, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from ddgs import DDGS
from models.schemas import AgentRequest, AgentResponse
from services.auth import verify_key
from services.rate_limiter import check_rate_limit
import os

router = APIRouter(prefix="/agent", tags=["Agent"])

@tool
def web_search(query: str):
    """Search the web for current information."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return "\n\n".join([
            f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}"
            for r in results
        ])
    except:
        return "Search failed."

RESEARCHER_PROMPT = """You are a research agent. Your job is to find information and answer the user's question.

Rules:
1. Call web_search AT MOST 3 TIMES.
2. If search returns empty, try a different query ONCE, then stop.
3. When you have enough information, write a concise answer with sources.
4. Always cite your sources."""

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here"),
    base_url="https://api.deepseek.com/v1"
)
llm_with_tools = llm.bind_tools([web_search])

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    research: str

def researcher_node(state: AgentState):
    messages = [{"role": "system", "content": RESEARCHER_PROMPT}] + state["messages"]
    response = llm_with_tools.invoke(messages)
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response]}
    else:
        state["research"] = response.content
        return {"messages": [response], "research": response.content}

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

builder = StateGraph(AgentState)
builder.add_node("researcher", researcher_node)
builder.add_node("tools", ToolNode([web_search]))
builder.set_entry_point("researcher")
builder.add_conditional_edges("researcher", should_continue, {"tools": "tools", "end": END})
builder.add_edge("tools", "researcher")

graph = builder.compile()

@router.post("", response_model=AgentResponse)
def agent_endpoint(request: AgentRequest, user=Depends(verify_key), _=Depends(check_rate_limit)):
    result = graph.invoke(
        {"messages": [{"role": "user", "content": request.question}], "research": ""},
        config={"recursion_limit": 10}
    )

    sources = []
    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            sources.append(msg.content[:200])

    return AgentResponse(
        answer=result["research"],
        sources=sources[-5:] if len(sources) > 0 else ["No sources found"]
    )