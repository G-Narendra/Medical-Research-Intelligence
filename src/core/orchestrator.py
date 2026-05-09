import os
import sys
from dotenv import load_dotenv
from typing import Dict

# Load environment
base_dir = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '.env'))
sys.path.append(base_dir)

from src.agents.query_router import MedicalQueryRouter
from src.agents.evaluation_agent import SelfEvaluationAgent, QueryRefinementAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.retrieval.medical_retriever import MedicalRetriever


class MedicalResearchOrchestrator:
    """
    Agentic RAG Orchestrator:
    Plan → Retrieve → Evaluate → Refine (if needed) → Synthesize
    """

    def __init__(self, max_iterations: int = 2):
        self.query_router = MedicalQueryRouter()
        self.retriever = MedicalRetriever()
        self.evaluator = SelfEvaluationAgent()
        self.refiner = QueryRefinementAgent()
        self.synthesizer = SynthesisAgent()
        self.max_iterations = max_iterations

    def run(self, user_query: str) -> Dict:
        """
        Main agentic loop.
        Returns dict with 'report', 'sources_used', 'iterations'
        """
        print(f"\n{'='*60}")
        print(f"MEDICAL RESEARCH INTELLIGENCE SYSTEM")
        print(f"Query: {user_query}")
        print(f"{'='*60}")

        all_retrieved_info = {"pubmed": [], "web": []}

        # Step 1: Plan
        print("\n[1/4] Analyzing query and creating retrieval plan...")
        try:
            plan = self.query_router.analyze_and_plan(user_query)
            print(f"  Intent: {plan.query_intent}")
            print(f"  Entities: {[e['name'] for e in plan.medical_entities]}")
            print(f"  Sources: {plan.sources_to_query}")
        except Exception as e:
            print(f"  Query router error: {e}. Using default plan.")
            from src.agents.query_router import QueryPlan
            plan = QueryPlan(
                medical_entities=[{"type": "general", "name": user_query}],
                query_intent="literature_review",
                sources_to_query=["pubmed", "web_search"],
                optimized_queries={"pubmed": user_query, "web_search": user_query},
                expected_info_types=["efficacy", "treatment", "research"]
            )

        # Step 2: Iterative retrieve → evaluate → refine
        for iteration in range(self.max_iterations):
            print(f"\n[2/4] Iteration {iteration + 1}: Retrieving from sources...")

            if "pubmed" in plan.sources_to_query:
                query = plan.optimized_queries.get("pubmed", user_query)
                print(f"  Searching PubMed: '{query}'")
                results = self.retriever.search_pubmed(query)
                print(f"  Found {len(results)} papers.")
                all_retrieved_info["pubmed"].extend(results)

            if "web_search" in plan.sources_to_query:
                query = plan.optimized_queries.get("web_search", user_query)
                print(f"  Searching Web: '{query}'")
                results = self.retriever.search_web(query)
                print(f"  Found {len(results)} web results.")
                all_retrieved_info["web"].extend(results)

            # Step 3: Self-evaluation
            print(f"\n[3/4] Evaluating sufficiency of retrieved information...")
            try:
                is_sufficient, reasoning, gaps = self.evaluator.evaluate(
                    user_query, all_retrieved_info, plan.expected_info_types
                )
                print(f"  Sufficient: {is_sufficient}")
                print(f"  Reasoning: {reasoning}")
            except Exception as e:
                print(f"  Evaluation error: {e}. Assuming sufficient.")
                is_sufficient = True
                gaps = []

            if is_sufficient or iteration == self.max_iterations - 1:
                print("  Information is sufficient. Proceeding to synthesis.")
                break
            else:
                # Step 4: Refine queries
                print(f"  Gaps found: {gaps}. Refining queries...")
                try:
                    refined_queries = self.refiner.refine(user_query, gaps)
                    plan.optimized_queries = refined_queries
                    plan.sources_to_query = list(refined_queries.keys())
                    plan.sources_to_query = [
                        "pubmed" if k == "pubmed" else "web_search"
                        for k in plan.sources_to_query
                    ]
                except Exception as e:
                    print(f"  Refinement error: {e}. Stopping iterations.")
                    break

        # Step 5: Synthesize final report
        print(f"\n[4/4] Synthesizing final research report...")
        report = self.synthesizer.synthesize(user_query, all_retrieved_info)
        print("  Report generated successfully.")

        return {
            "report": report,
            "sources_used": {
                "pubmed_count": len(all_retrieved_info["pubmed"]),
                "web_count": len(all_retrieved_info["web"]),
                "pubmed_papers": all_retrieved_info["pubmed"],
                "web_results": all_retrieved_info["web"],
            },
            "iterations": iteration + 1
        }
