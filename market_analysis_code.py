from langgraph.graph import StateGraph
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.callbacks import tracing_v2_enabled
from typing import TypedDict
from dotenv import load_dotenv
import os
import requests

load_dotenv()

class MarketState(TypedDict):
    query: str
    web_results: str
    internal_docs: str
    insights: str
    swot_report: str

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def web_search_agent(state: MarketState):
    with tracing_v2_enabled(project_name="AI Market Analyst - Web Search Agent"):
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {TAVILY_API_KEY}"},
                json={"query": state["query"], "max_results": 3}
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            summary = "\n".join([item["content"] for item in results])
            state["web_results"] = summary or "No relevant web data found."
        except Exception as e:
            state["web_results"] = f"Error fetching web data: {e}"
        return state

def internal_retriever_agent(state: MarketState):
    with tracing_v2_enabled(project_name="AI Market Analyst - Internal Retriever Agent"):
        db = FAISS.load_local(
            "faiss_index",
            GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
            allow_dangerous_deserialization=True
        )
        docs = db.similarity_search(state["query"], k=3)
        state["internal_docs"] = "\n\n".join([d.page_content for d in docs])
        return state

def insight_generator_agent(state: MarketState):
    with tracing_v2_enabled(project_name="AI Market Analyst - Insight Generator Agent"):
        prompt = PromptTemplate.from_template("""
        Using the internal documents and web results, summarize market insights:
        Internal:
        {internal}
        Web:
        {web}
        """)
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        chain = prompt | llm
        result = chain.invoke({"internal": state["internal_docs"], "web": state["web_results"]})
        state["insights"] = result.content
        return state

def swot_agent(state: MarketState):
    with tracing_v2_enabled(project_name="AI Market Analyst - SWOT Agent"):
        prompt = PromptTemplate.from_template("""
        Generate a SWOT Analysis based on the following:
        {insights}
        Format as:
        Strengths:\n...
        Weaknesses:\n...
        Opportunities:\n...
        Threats:\n...
        """)
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        chain = prompt | llm
        result = chain.invoke({"insights": state["insights"]})
        state["swot_report"] = result.content
        return state

def get_graph():
    workflow = StateGraph(MarketState)
    workflow.add_node("web_search", web_search_agent)
    workflow.add_node("internal_retriever", internal_retriever_agent)
    workflow.add_node("generate_insights", insight_generator_agent)
    workflow.add_node("generate_swot", swot_agent)
    workflow.set_entry_point("web_search")
    workflow.add_edge("web_search", "internal_retriever")
    workflow.add_edge("internal_retriever", "generate_insights")
    workflow.add_edge("generate_insights", "generate_swot")
    workflow.set_finish_point("generate_swot")
    return workflow.compile()
