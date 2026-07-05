import streamlit as st
import os
import asyncio
import re
from dotenv import load_dotenv

# Load env variables (for GEMINI_API_KEY)
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Project Intelligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
    }
    
    /* Header styling */
    .title-container {
        padding: 1.5rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .title-container h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .title-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* KPI Card styling */
    .kpi-card {
        background: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #2a5298;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .kpi-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #6c757d;
        font-weight: 600;
    }
    
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #212529;
        margin-top: 0.25rem;
    }
    
    /* Factor card styling */
    .factor-card {
        background: white;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    
    .factor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .factor-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3c72;
    }
    
    .badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-weight: 600;
    }
    
    .badge-high {
        background-color: #d1e7dd;
        color: #0f5132;
    }
    
    .badge-medium {
        background-color: #fff3cd;
        color: #664d03;
    }
    
    .badge-low {
        background-color: #f8d7da;
        color: #842029;
    }
    
    /* Log block styling */
    .log-container {
        background: #1e1e1e;
        color: #a9b7c6;
        font-family: 'Courier New', Courier, monospace;
        padding: 1rem;
        border-radius: 8px;
        max-height: 300px;
        overflow-y: auto;
        font-size: 0.9rem;
        line-height: 1.4;
        margin-bottom: 1.5rem;
        border-left: 4px solid #4CAF50;
    }
    
    .log-line {
        margin-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="title-container">
    <h1>PROJECT INTELLIGENCE AGENT</h1>
    <p>Investigative Multi-Agent AI System for Post-Mortem Analysis</p>
</div>
""", unsafe_allow_html=True)

# Check API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.warning("⚠️ GEMINI_API_KEY environment variable not set. Please set it in the sidebar or in your local `.env` file.")

# Sidebar Settings
st.sidebar.title("📁 Document Upload & Options")

# File Upload Section
uploaded_files = st.sidebar.file_uploader(
    "Upload project files (Jira CSV, Retrospective PDFs, Slack TXT)",
    type=["csv", "pdf", "txt"],
    accept_multiple_files=True
)

st.sidebar.markdown("---")
st.sidebar.subheader("Preloaded Datasets")
st.sidebar.info(
    "Three sample datasets are preloaded:\n"
    "- Project Phoenix\n"
    "- Project Apollo\n"
    "- Project Nebula\n\n"
    "The Planner Agent automatically identifies and filters to the correct project's files."
)

# Get active files
temp_files = []
active_filenames = []
valid_uploads = True

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'.csv', '.pdf', '.txt'}

if uploaded_files:
    # Save uploaded files to temp folder in workspace
    os.makedirs("temp_uploads", exist_ok=True)
    for f in uploaded_files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            st.sidebar.error(f"❌ File {f.name} has an invalid format. Only CSV, PDF, and TXT are allowed.")
            valid_uploads = False
            break
        if f.size > MAX_FILE_SIZE:
            st.sidebar.error(f"❌ File {f.name} exceeds the 5MB size limit.")
            valid_uploads = False
            break
            
        path = os.path.join("temp_uploads", f.name)
        with open(path, "wb") as file_out:
            file_out.write(f.getbuffer())
        temp_files.append(path)
        active_filenames.append(f.name)
else:
    # Load all demo datasets at startup
    demo_dir = "data"
    if os.path.exists(demo_dir):
        for f in os.listdir(demo_dir):
            f_lower = f.lower()
            if any(f_lower.startswith(p) for p in ["phoenix_", "apollo_", "nebula_"]):
                path = os.path.join(demo_dir, f)
                if os.path.isfile(path) and os.path.splitext(f)[1].lower() in ['.csv', '.pdf', '.txt']:
                    temp_files.append(path)
                    active_filenames.append(f)
                    
# Display loaded files list in sidebar
if active_filenames:
    st.sidebar.success(f"Loaded {len(active_filenames)} files:")
    for fn in active_filenames:
        st.sidebar.markdown(f"- `{fn}`")
else:
    st.sidebar.info("No files loaded. Upload files or select a preloaded dataset above.")

# Main area
st.subheader("💡 Investigate your project")
query_input = st.text_input(
    "What project bottleneck or delay would you like to investigate?",
    value="Why was Project Phoenix delayed 6 weeks?",
    placeholder="e.g. Why was Project Phoenix delayed? or Which team caused the bottleneck in Sprint 3?"
)
st.markdown("""
<div style="color: gray; font-size: 0.85rem; margin-top: -12px; margin-bottom: 12px; font-style: italic;">
<strong>Example Questions:</strong><br/>
• "Why was the project delayed?"<br/>
• "What were the major blockers?"<br/>
• "Which sprint had the most issues?"<br/>
• "What risks should have been detected earlier?"
</div>
""", unsafe_allow_html=True)

analyze_button = st.button("🚀 Run Investigation", type="primary")

if analyze_button:
    if not valid_uploads:
        st.error("Please resolve file upload validation errors before running.")
    elif not temp_files:
        st.error("Please upload documents or check the 'Use preloaded' dataset option.")
    elif not query_input.strip():
        st.error("Please enter a question.")
    elif not api_key:
        st.error("GEMINI_API_KEY is required to run the pipeline. Add it to the .env file in the workspace.")
    else:
        st.markdown("---")
        st.subheader("⚙️ Agent Pipeline Execution")
        
        # Log container
        log_placeholder = st.empty()
        log_text = []
        
        # Function to update log UI
        def update_log(msg: str):
            log_text.append(f"<div class='log-line'>[{len(log_text)+1}] {msg}</div>")
            log_placeholder.markdown(
                f"<div class='log-container'>{''.join(log_text)}</div>",
                unsafe_allow_html=True
            )
            
        # Pipeline Runner implementation
        async def run_pipeline():
            # Import documents and chunking
            from document_loader import chunk_documents
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types
            from agents_workflow import workflow
            
            update_log("Document parsing started...")
            chunks = chunk_documents(temp_files)
            update_log(f"Parsed {len(chunks)} chunks from {len(temp_files)} documents.")
            
            # Setup session
            session_service = InMemorySessionService()
            runner = Runner(session_service=session_service, node=workflow, auto_create_session=True)
            
            msg = types.Content(role="user", parts=[types.Part(text=query_input)])
            
            state_delta = {
                "file_chunks": chunks,
                "uploaded_files": active_filenames,
                "user_question": query_input,
                "retry_count": 0,
                "gap_description": ""
            }
            
            update_log("Initializing agent workflow graph...")
            final_report = None
            
            async for event in runner.run_async(
                user_id="streamlit_user",
                session_id="session_1",
                new_message=msg,
                state_delta=state_delta
            ):
                node_name = ""
                if event.node_info and event.node_info.path:
                    parts = event.node_info.path.split('/')
                    if len(parts) > 1:
                        node_name = parts[-1].split('@')[0]
                if not node_name:
                    node_name = event.author or ""
                
                if node_name:
                    
                    if event.error_message:
                        update_log(f"❌ Error in Agent `{node_name}`: {event.error_message}")
                    elif event.output is not None:
                        # Event output produced
                        if node_name == "run_planner":
                            update_log("📋 Planner Agent generated search strategy queries.")
                            if event.output and hasattr(event.output, 'question_type'):
                                st.session_state["detected_inv_type"] = event.output.question_type
                            if event.output and hasattr(event.output, 'target_project'):
                                st.session_state["detected_target_project"] = event.output.target_project
                        elif node_name == "retriever_node":
                            update_log("🔍 Retriever Node executed queries and pulled matching chunks.")
                        elif node_name == "run_investigator":
                            update_log("🔎 Investigator Agent reconstructed timeline and analyzed root-cause factors.")
                        elif node_name == "run_reporter":
                            update_log("🗄️ Reporter Agent compiled final report and recommendations.")
                            final_report = event.output
                        
            return final_report

        # Run pipeline in event loop
        with st.spinner("Analyzing project data (running agent pipeline)..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                report = loop.run_until_complete(run_pipeline())
                loop.close()
                
                if report:
                    if isinstance(report, dict):
                        from models import FinalReport
                        report = FinalReport(**report)
                    st.success("Investigation complete! Final report compiled below.")
                    st.markdown("---")
                    
                    # Display Final Report
                    st.header("📋 Post-Mortem Report")
                    detected_type = st.session_state.get("detected_inv_type", "General Analysis")
                    st.markdown(f"**Detected Investigation Type:** `{detected_type}`")
                    
                    # KPI summary cards
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-title">Overall Analysis Confidence</div>
                            <div class="kpi-value">{report.confidence*100:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-title">Contributing Factors</div>
                            <div class="kpi-value">{len(report.contributing_factors)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="kpi-card" style="border-left-color: #28a745;">
                            <div class="kpi-title">Recommendations Map</div>
                            <div class="kpi-value">{len(report.recommendations)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    if report.report_type == "comparison":
                        tab_titles = [
                            "📊 Executive Comparison Table & AI Insights", 
                            "⚖️ Shared/Unique Issues", 
                            "📅 Timeline Comparison"
                        ]
                        tab1, tab2, tab3 = st.tabs(tab_titles)
                        
                        with tab1:
                            st.markdown("### Executive Comparison")
                            st.markdown(report.executive_summary)
                            
                            # Render properly formatted table natively in Streamlit
                            import pandas as pd
                            if report.comparison_table:
                                try:
                                    df = pd.DataFrame(report.comparison_table)
                                    st.table(df)
                                except Exception as e:
                                    st.warning(f"Could not render comparison table: {e}")
                                    st.write(report.comparison_table)
                                    
                            st.markdown("### Source Documents Investigated")
                            for source in report.source_documents:
                                st.markdown(f"- 📄 `{source}`")
                                
                        with tab2:
                            st.markdown(report.shared_vs_unique_issues)
                            
                        with tab3:
                            st.markdown("### Category-by-Category Timeline Comparison")
                            st.markdown(report.comparison_insights)
                    else:
                        # Standard single project mode
                        tab_titles = [
                            "📝 Executive Summary", 
                            "⚖️ Contributing Factors", 
                            "📅 Event Timeline", 
                            "💡 Action Plan"
                        ]
                        tab1, tab2, tab3, tab4 = st.tabs(tab_titles)
                        
                        with tab1:
                            st.markdown("### Executive Summary")
                            st.markdown(report.executive_summary)
                            
                            st.markdown("### Source Documents Investigated")
                            for source in report.source_documents:
                                st.markdown(f"- 📄 `{source}`")
                                
                        with tab2:
                            st.markdown("### Key Contributing Factors")
                            for factor in report.contributing_factors:
                                conf = factor.confidence
                                badge_class = "badge-high" if conf >= 0.8 else ("badge-medium" if conf >= 0.5 else "badge-low")
                                
                                st.markdown(f"""
                                <div class="factor-card">
                                    <div class="factor-header">
                                        <span class="factor-title">[{factor.factor_id}] {factor.factor_name}</span>
                                        <span class="badge {badge_class}">Confidence: {conf*100:.0f}%</span>
                                    </div>
                                    <p style="color: #495057; margin-bottom: 0.75rem;">{factor.description}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                with st.expander(f"🔍 View Supporting Evidence ({len(factor.evidence_refs)} quotes)"):
                                    for ref in factor.evidence_refs:
                                        st.info(ref)
                                        
                        with tab3:
                            st.markdown("### Reconstructed Chronological Timeline")
                            timeline_data = []
                            for ev in report.timeline:
                                timeline_data.append({
                                    "Date/Sprint": ev.date,
                                    "Event Description": ev.event_description,
                                    "Source Citation": ev.source_citation,
                                    "Date Confidence": ev.date_confidence.upper()
                                })
                            st.table(timeline_data)
                            
                        with tab4:
                            st.markdown("### Actionable Recommendations")
                            for rec in report.recommendations:
                                factor_name = next(
                                    (f.factor_name for f in report.contributing_factors if f.factor_id == rec.factor_id),
                                    "Unknown Factor"
                                )
                                st.markdown(f"**Recommendation `{rec.recommendation_id}`** (Tied to: *{factor_name}*)")
                                st.info(rec.suggested_action)
                else:
                    st.error("Failed to compile final report. Please check the logs above.")
            except Exception as e:
                st.exception(e)
                st.error("An error occurred during execution. Please verify your GEMINI_API_KEY is correct.")
