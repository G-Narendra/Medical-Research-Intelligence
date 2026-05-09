from typing import Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI


class SynthesisAgent:
    """
    Synthesizes information from all sources into a structured medical research report.
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.2)

    def synthesize(self, user_query: str, retrieved_info: Dict) -> str:
        """Generate a comprehensive, cited medical research report."""

        # Build context from PubMed papers
        pubmed_context = ""
        for i, paper in enumerate(retrieved_info.get("pubmed", [])[:8], 1):
            pubmed_context += f"""
[{i}] Title: {paper.get('title', 'N/A')}
    Authors: {', '.join(paper.get('authors', []))} ({paper.get('year', 'N/A')})
    Journal: {paper.get('journal', 'N/A')}
    Abstract: {paper.get('abstract', 'N/A')[:500]}
    PMID: {paper.get('pmid', 'N/A')} | URL: {paper.get('url', '')}
"""

        # Build context from web sources
        web_context = ""
        ref_start = len(retrieved_info.get("pubmed", [])) + 1
        for i, result in enumerate(retrieved_info.get("web", [])[:5], ref_start):
            web_context += f"""
[{i}] Title: {result.get('title', 'N/A')}
    Content: {result.get('content', 'N/A')[:400]}
    URL: {result.get('url', '')}
"""

        prompt = f"""You are a senior medical research analyst. Synthesize the retrieved information into a comprehensive, structured report.

USER QUERY: {user_query}

== PUBMED RESEARCH PAPERS ==
{pubmed_context if pubmed_context else "No PubMed results available."}

== WEB / CLINICAL TRIAL SOURCES ==
{web_context if web_context else "No web results available."}

Generate a comprehensive report with these EXACT sections:

## Executive Summary
(2-3 sentence overview of key findings)

## Key Findings
(Bullet points with evidence levels: [High/Moderate/Low Evidence])

## Treatment Options
(Ranked by evidence strength, cite sources using [1], [2] etc.)

## Drug Information
(If relevant: mechanisms, dosing, side effects, interactions)

## Clinical Trial Updates
(Recent trials, ongoing studies, findings)

## References
(APA format for all cited sources)

## ⚠️ Medical Disclaimer
Include: "This is for educational/research purposes only. Always consult a licensed medical professional for clinical decisions."

Be comprehensive, accurate, and cite all sources."""

        response = self.llm.invoke(prompt)
        return response.content
