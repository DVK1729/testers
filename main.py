from fastapi import FastAPI
from pydantic import BaseModel
from market_analysis_code import get_graph
from dotenv import load_dotenv
from langchain.callbacks import tracing_v2_enabled

load_dotenv()

app = FastAPI()
graph = get_graph()

class Query(BaseModel):
    query: str

@app.post("/analyze")
async def analyze(q: Query):
    with tracing_v2_enabled(project_name="AI Market Analyst - SWOT Analysis API"):
        result = graph.invoke({"query": q.query})
        return {"swot_report": result["swot_report"]}
