import json
import os
from typing import Dict, List
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI


class QueryPlan(BaseModel):
    """Structured plan for information gathering"""
    medical_entities: List[Dict]
    query_intent: str
    sources_to_query: List[str]
    optimized_queries: Dict[str, str]
    expected_info_types: List[str]


class MedicalQueryRouter:
    """
    Analyzes medical queries using Gemini and creates a structured retrieval plan.
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1)

    def analyze_and_plan(self, user_query: str) -> QueryPlan:
        system_prompt = """You are a medical information retrieval specialist.
Analyze the user's medical query and return a JSON object with EXACTLY these fields:
{
  "medical_entities": [{"type": "disease|drug|procedure|symptom", "name": "..."}],
  "query_intent": "literature_review|drug_information|treatment_options|diagnosis|clinical_trial",
  "sources_to_query": ["pubmed", "web_search"],
  "optimized_queries": {"pubmed": "...", "web_search": "..."},
  "expected_info_types": ["efficacy", "side_effects", "dosage", "mechanism", "trials"]
}
Return ONLY valid JSON, no markdown, no explanation."""

        response = self.llm.invoke(
            f"{system_prompt}\n\nQuery: {user_query}\n\nCreate retrieval plan:"
        )
        
        # Clean response and parse
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        plan_data = json.loads(content)
        return QueryPlan(**plan_data)
