import json
from typing import Dict, List, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI


class SelfEvaluationAgent:
    """
    Evaluates whether retrieved information is sufficient.
    Returns (is_sufficient: bool, reasoning: str, gaps: List[str])
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.0)

    def evaluate(
        self,
        user_query: str,
        retrieved_info: Dict,
        expected_info_types: List[str]
    ) -> Tuple[bool, str, List[str]]:

        pubmed_count = len(retrieved_info.get("pubmed", []))
        web_count = len(retrieved_info.get("web", []))

        summary = f"PubMed papers: {pubmed_count}, Web results: {web_count}"
        pubmed_titles = [p.get("title", "") for p in retrieved_info.get("pubmed", [])[:3]]
        web_titles = [w.get("title", "") for w in retrieved_info.get("web", [])[:3]]

        prompt = f"""You are a medical research quality evaluator.

User Query: {user_query}
Expected Information Types: {expected_info_types}
Retrieved: {summary}
Sample PubMed Titles: {pubmed_titles}
Sample Web Titles: {web_titles}

Evaluate if this is sufficient for a comprehensive medical answer.
Return JSON only:
{{
  "is_sufficient": true/false,
  "reasoning": "brief explanation",
  "gaps": ["missing aspect 1", "missing aspect 2"]
}}"""

        response = self.llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content.strip())
        return result["is_sufficient"], result["reasoning"], result.get("gaps", [])


class QueryRefinementAgent:
    """
    Given identified gaps, generates refined queries for another retrieval round.
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.1)

    def refine(self, original_query: str, gaps: List[str]) -> Dict[str, str]:

        prompt = f"""You are a medical search specialist.

Original Query: {original_query}
Information Gaps Identified: {gaps}

Generate refined search queries to fill these gaps.
Return JSON only:
{{
  "pubmed": "optimized PubMed query for the gaps",
  "web_search": "optimized web search query for the gaps"
}}"""

        response = self.llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content.strip())
