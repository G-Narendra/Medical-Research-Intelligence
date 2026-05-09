import os
import sys
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))
sys.path.append(base_dir)

from src.core.orchestrator import MedicalResearchOrchestrator
from langchain_google_genai import ChatGoogleGenerativeAI


def run_evaluation():
    """
    Model-as-a-Judge evaluation against 10 medical queries.
    """
    print("=" * 60)
    print("MEDICAL RESEARCH INTELLIGENCE - EVALUATION")
    print("=" * 60)

    orchestrator = MedicalResearchOrchestrator(max_iterations=2)
    judge_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.0)

    golden_dataset = [
        {
            "query": "Latest treatments for Type 2 Diabetes",
            "expected_concepts": ["metformin", "GLP-1", "SGLT2", "insulin", "lifestyle"],
        },
        {
            "query": "Side effects of metformin",
            "expected_concepts": ["gastrointestinal", "lactic acidosis", "vitamin B12", "nausea"],
        },
        {
            "query": "Recent clinical trials for Alzheimer's disease",
            "expected_concepts": ["amyloid", "tau", "lecanemab", "clinical trial", "phase"],
        },
        {
            "query": "COVID-19 long-term cardiovascular complications",
            "expected_concepts": ["myocarditis", "thrombosis", "long COVID", "cardiac", "inflammation"],
        },
        {
            "query": "Efficacy of GLP-1 agonists for obesity",
            "expected_concepts": ["semaglutide", "weight loss", "BMI", "randomized", "trial"],
        },
    ]

    passed = 0
    total_iterations = 0

    for i, item in enumerate(golden_dataset, 1):
        print(f"\n[{i}/{len(golden_dataset)}] Query: {item['query']}")
        try:
            result = orchestrator.run(item["query"])
            report = result["report"]
            iters = result["iterations"]
            total_iterations += iters

            judge_prompt = f"""Medical research report evaluation.
Expected concepts that should appear: {item['expected_concepts']}
Generated report (first 800 chars): {report[:800]}

Does the report cover at least 3 of the expected concepts? Answer only PASS or FAIL."""

            verdict = judge_llm.invoke(judge_prompt).content.strip().upper()
            verdict_str = "[PASS]" if "PASS" in verdict else "[FAIL]"
            if "PASS" in verdict:
                passed += 1

            print(f"  Sources: {result['sources_used']['pubmed_count']} PubMed + {result['sources_used']['web_count']} Web")
            print(f"  Iterations: {iters} | Verdict: {verdict_str}")

        except Exception as e:
            print(f"  ERROR: {e}")

    accuracy = (passed / len(golden_dataset)) * 100
    avg_iter = total_iterations / len(golden_dataset)

    print(f"\n{'='*60}")
    print(f"EVALUATION COMPLETE")
    print(f"Score: {passed}/{len(golden_dataset)} ({accuracy:.1f}% accuracy)")
    print(f"Avg iterations per query: {avg_iter:.1f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_evaluation()
