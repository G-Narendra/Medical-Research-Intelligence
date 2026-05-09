import os
import sys
import streamlit as st
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, '.env'))
sys.path.append(base_dir)

from src.core.orchestrator import MedicalResearchOrchestrator


@st.cache_resource
def init_orchestrator():
    return MedicalResearchOrchestrator(max_iterations=2)


def main():
    st.set_page_config(
        page_title="Medical Research Intelligence System",
        page_icon="🧬",
        layout="wide"
    )

    # Header
    st.title("🧬 Medical Research Intelligence System")
    st.markdown("*Agentic RAG — Powered by PubMed, Tavily Web Search & Google Gemini*")
    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Info")
        st.info("**Sources:** PubMed (peer-reviewed papers) + Web Search (Clinical Trials, FDA, WHO)")
        st.info("**Pipeline:** Query Analysis → Multi-Source Retrieval → Self-Evaluation → Refinement → Synthesis")
        st.info("**Model:** Gemini 2.5 Flash Lite")
        st.divider()
        st.markdown("### 💡 Example Queries")
        examples = [
            "Latest treatments for Type 2 Diabetes in UAE",
            "Efficacy of GLP-1 agonists for obesity",
            "Recent clinical trials for Alzheimer's disease",
            "Side effects of metformin and alternatives",
            "COVID-19 long-term cardiovascular complications"
        ]
        for ex in examples:
            if st.button(ex, key=ex):
                st.session_state.query = ex
                st.session_state.auto_run = True

    # Main interface
    try:
        orchestrator = init_orchestrator()
    except Exception as e:
        st.error(f"Initialization failed: {e}")
        st.stop()

    with st.form("search_form"):
        query = st.text_area(
            "Enter your medical research query:",
            value=st.session_state.get("query", ""),
            height=80,
            placeholder="e.g., Latest treatments for Type 2 Diabetes in UAE"
        )
        col1, col2 = st.columns([1, 4])
        with col1:
            submit = st.form_submit_button("🔍 Research", type="primary", use_container_width=True)

    if submit or st.session_state.get("auto_run", False):
        st.session_state.auto_run = False
        if not query.strip():
            st.warning("Please enter a medical research query.")
        else:
            # Live agent status
            status_container = st.container()
            with status_container:
                with st.spinner("🤖 Agent is working..."):

                    step1 = st.status("📋 Step 1: Analyzing query intent and planning...", expanded=False)
                    step2 = st.status("🔎 Step 2: Retrieving from PubMed & Web...", expanded=False)
                    step3 = st.status("🧠 Step 3: Self-evaluating information quality...", expanded=False)
                    step4 = st.status("✍️ Step 4: Synthesizing final report...", expanded=False)

                    try:
                        result = orchestrator.run(query)

                        step1.update(label="✅ Step 1: Query plan created.", state="complete")
                        step2.update(label=f"✅ Step 2: Retrieved {result['sources_used']['pubmed_count']} papers + {result['sources_used']['web_count']} web results.", state="complete")
                        step3.update(label=f"✅ Step 3: Completed in {result['iterations']} iteration(s).", state="complete")
                        step4.update(label="✅ Step 4: Report synthesized.", state="complete")

                        st.divider()
                        st.markdown("## 📄 Research Report")
                        st.markdown(result["report"])

                        # Sources tab
                        st.divider()
                        with st.expander(f"📚 View All Sources ({result['sources_used']['pubmed_count']} PubMed + {result['sources_used']['web_count']} Web)"):
                            tab1, tab2 = st.tabs(["PubMed Papers", "Web Sources"])

                            with tab1:
                                for paper in result["sources_used"]["pubmed_papers"]:
                                    st.markdown(f"**{paper.get('title', 'N/A')}**")
                                    st.caption(f"*{', '.join(paper.get('authors', []))} — {paper.get('journal', 'N/A')} ({paper.get('year', 'N/A')})*")
                                    st.markdown(f"🔗 [PMID: {paper.get('pmid')}]({paper.get('url', '')})")
                                    st.markdown(paper.get("abstract", "")[:300] + "...")
                                    st.divider()

                            with tab2:
                                for r in result["sources_used"]["web_results"]:
                                    st.markdown(f"**{r.get('title', 'N/A')}**")
                                    st.markdown(r.get("content", "")[:300] + "...")
                                    st.markdown(f"🔗 [{r.get('url', '')}]({r.get('url', '')})")
                                    st.divider()

                    except Exception as e:
                        step1.update(state="error")
                        st.error(f"Error during research pipeline: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    st.caption("⚠️ For educational and research purposes only. Always consult a licensed medical professional.")


if __name__ == "__main__":
    main()
