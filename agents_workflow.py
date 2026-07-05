import asyncio
import re
from typing import Any
from google.adk import Workflow, Context
from google.adk.agents import LlmAgent
from google.adk.workflow import Edge, START, node
from google.genai import types

# Import schemas and search tool
from models import (
    PlannerOutput, InvestigatorOutput, FinalReport,
    TimelineEvent, ContributingFactor, Recommendation
)
from search_tool import search_project_documents

# 1. Define Core LlmAgents (Maximum 2 Gemini calls: Planner and Reporter)
planner_agent = LlmAgent(
    name="planner_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Planner Agent. Parse the user's question, identify the project(s) explicitly referenced (Phoenix, Apollo, Nebula).\n"
        "1. If specific project names are explicitly mentioned, set target_project to a comma-separated list of those project names (e.g. 'Phoenix, Apollo' or 'Nebula').\n"
        "2. If no project names are explicitly mentioned in the query, set target_project to 'All' if it is a comparison or cross-project query, or 'Ambiguous' if it is ambiguous.\n"
        "3. Determine the investigation type (question_type) from the query, matching one of: 'Root Cause Analysis', 'Project Comparison', 'Timeline Reconstruction', 'Risk Assessment', 'Dependency Analysis', 'Resource Bottlenecks'.\n"
        "Generate a structured retrieval plan using the PlannerOutput schema, defining evidence types and targeted search queries."
    ),
    output_schema=PlannerOutput
)

report_agent = LlmAgent(
    name="report_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Report Agent. Review the timeline of events and contributing factors.\n"
        "Produce a plain JSON object representing the post-mortem report. Do not return any markdown format, text, or conversational intro/outro before or after the JSON. "
        "The JSON MUST follow this exact schema structure:\n\n"
        "{\n"
        "  \"report_type\": \"single\" or \"comparison\",\n"
        "  \"executive_summary\": \"[Markdown text executive summary (for single) or comparison overview (for comparison)]\",\n"
        "  \"contributing_factors\": [\n"
        "    {\n"
        "      \"factor_id\": \"F1\",\n"
        "      \"factor_name\": \"...\",\n"
        "      \"description\": \"...\",\n"
        "      \"confidence\": 0.85,\n"
        "      \"evidence_refs\": [\"...\"]\n"
        "    }\n"
        "  ],\n"
        "  \"timeline\": [\n"
        "    {\n"
        "      \"date\": \"...\",\n"
        "      \"event_description\": \"...\",\n"
        "      \"source_citation\": \"...\",\n"
        "      \"date_confidence\": \"high\" or \"medium\" or \"low\"\n"
        "    }\n"
        "  ],\n"
        "  \"source_documents\": [\"...\"],\n"
        "  \"confidence\": 0.90,\n"
        "  \"comparison_table\": [ {\"Metric\": \"...\", \"Project Phoenix\": \"...\", \"Project Apollo/Nebula\": \"...\"} ],\n"
        "  \"shared_vs_unique_issues\": \"[Markdown text comparing shared and project-specific factors]\",\n"
        "  \"comparison_insights\": \"[Markdown text containing category-by-category timeline contrast and AI insights]\",\n"
        "  \"recommendations\": [\n"
        "    {\n"
        "      \"recommendation_id\": \"R1\",\n"
        "      \"factor_id\": \"F1\",\n"
        "      \"suggested_action\": \"...\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
)

# 2. Define Workflow Nodes

@node(name="run_planner", rerun_on_resume=True)
async def run_planner(ctx: Context, node_input: Any) -> PlannerOutput:
    # Extract user question from types.Content or state
    if isinstance(node_input, types.Content):
        user_q = "".join(part.text for part in node_input.parts if part.text)
        ctx.state["user_question"] = user_q
    else:
        user_q = ctx.state.get("user_question", "")
            
    files_list = ctx.state.get("uploaded_files", [])
    prompt = f"User Question: {user_q}\nUploaded Files: {', '.join(files_list)}"
    
    print(f"[Planner] Running planner agent...")
    res = await ctx.run_node(planner_agent, node_input=prompt)
    if isinstance(res, dict):
        res = PlannerOutput(**res)
    ctx.state["target_project"] = res.target_project
    print(f"[Planner] Generated plan with {len(res.search_queries)} queries for project: {res.target_project}.")
    return res

@node(name="retriever_node")
async def retriever_node(ctx: Context, node_input: Any) -> str:
    plan = node_input
    if isinstance(plan, dict):
        plan = PlannerOutput(**plan)
        
    target = getattr(plan, "target_project", "All")
    if not target:
        target = "All"
    target = target.strip().lower()
    ctx.state["target_project"] = plan.target_project
    
    if target == "ambiguous":
        ctx.state["is_ambiguous"] = True
        print("[Retriever] Target project is ambiguous. Flagging for user clarification.")
        return "Ambiguous query: no project specified."
        
    ctx.state["is_ambiguous"] = False
    print(f"[Retriever] Programmatic retrieval for queries: {plan.search_queries} targeting project: {plan.target_project}")
    evidence_results = []
    
    # Save the original file chunks
    all_chunks = ctx.state.get("file_chunks", [])
    
    if "all" not in target:
        targets = [t.strip() for t in target.split(",") if t.strip()]
        print(f"[Retriever] Restricting retrieval to projects: {targets}")
        filtered_chunks = []
        for chunk in all_chunks:
            source_lower = chunk.get("source", "").lower()
            if any(p in source_lower for p in targets):
                filtered_chunks.append(chunk)
        if filtered_chunks:
            ctx.state["file_chunks"] = filtered_chunks
        else:
            print(f"[Retriever] Warning: No chunks found matching target projects {targets}. Using all chunks.")
            
    for query in plan.search_queries:
        res = search_project_documents(query=query, ctx=ctx)
        evidence_results.append(res)
        
    # Restore original file chunks
    ctx.state["file_chunks"] = all_chunks
    
    merged_evidence = "\n\n".join(evidence_results)
    
    # Python validation: check if we found any evidence
    clean_evidence = merged_evidence.replace("No matching evidence found in the documents.", "").strip()
    if len(clean_evidence) < 50:
        warning_msg = "Warning: Programmatic search returned very little or no relevant evidence chunks."
        print(warning_msg)
        merged_evidence += f"\n\n{warning_msg}"
        
    ctx.state["retrieved_evidence"] = merged_evidence
    print(f"[Retriever] Ingested evidence of length {len(merged_evidence)} chars.")
    return merged_evidence

@node(name="run_investigator", rerun_on_resume=True)
async def run_investigator(ctx: Context, node_input: Any) -> InvestigatorOutput:
    if ctx.state.get("is_ambiguous", False):
        res = InvestigatorOutput(timeline=[], contributing_factors=[])
        ctx.state["investigator_output"] = res.model_dump()
        return res
        
    print(f"[Investigator] Running dynamic keyword-based Python investigation...")
    
    # Define analysis categories and keywords
    categories = {
        "blocker": {
            "name": "Process & Dependency Blockers",
            "keywords": ["blocked", "waiting", "dependency", "delayed", "on hold"],
            "hits": 0,
            "evidence": []
        },
        "scope_creep": {
            "name": "Scope Creep & Requirement Changes",
            "keywords": ["added", "new requirement", "scope change", "out of scope", "additional"],
            "hits": 0,
            "evidence": []
        },
        "resource": {
            "name": "Resource Constraints & Sickness Outages",
            "keywords": ["sick", "leave", "unavailable", "underresourced", "short-staffed"],
            "hits": 0,
            "evidence": []
        }
    }
    
    timeline_events = []
    all_chunks = ctx.state.get("file_chunks", [])
    target = ctx.state.get("target_project", "All")
    if not target:
        target = "All"
    target = target.strip().lower()
    
    if "all" not in target:
        targets = [t.strip() for t in target.split(",") if t.strip()]
        print(f"[Investigator] Restricting analysis to projects: {targets}")
        chunks = []
        for chunk in all_chunks:
            source_lower = chunk.get("source", "").lower()
            if any(p in source_lower for p in targets):
                chunks.append(chunk)
        if not chunks:
            chunks = all_chunks
    else:
        chunks = all_chunks
        
    total_chunks = len(chunks) if chunks else 1
    
    for chunk in chunks:
        content = chunk.get("content", "")
        source = chunk.get("source", "")
        location = chunk.get("location", "")
        
        # 1. Extract dates using regex
        # Pattern: YYYY-MM-DD
        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', content + " " + location)
        date_val = ""
        date_conf = "high"
        
        if date_match:
            date_val = date_match.group(1)
        else:
            # Fallback to Sprint names
            sprint_match = re.search(r'\b(Sprint\s+\d+)\b', content + " " + location, re.IGNORECASE)
            if sprint_match:
                date_val = sprint_match.group(1).title()
                date_conf = "medium"
            else:
                date_val = "Undated"
                date_conf = "low"
        
        content_lower = content.lower()
        
        # 2. Detect matching patterns in this chunk
        for cat_id, cat_info in categories.items():
            matched_kws = [kw for kw in cat_info["keywords"] if kw in content_lower]
            if matched_kws:
                cat_info["hits"] += 1
                
                # Extract the line containing the keyword for evidence
                matching_lines = []
                for line in content.split('\n'):
                    line_lower = line.lower()
                    if any(kw in line_lower for kw in matched_kws):
                        matching_lines.append(line.strip())
                
                snippet = matching_lines[0] if matching_lines else content[:120].strip()
                evidence_str = f"[{source} at {location}] {snippet}"
                cat_info["evidence"].append(evidence_str)
                
                # Create timeline event if a date/sprint is available
                if date_val != "Undated":
                    timeline_events.append(TimelineEvent(
                        date=date_val,
                        event_description=f"[{cat_info['name']}] {snippet}",
                        source_citation=f"{source} ({location})",
                        date_confidence=date_conf
                    ))

    # Sort timeline events chronologically
    def get_sort_key(event: TimelineEvent) -> tuple:
        match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', event.date)
        if match:
            return (0, match.group(1))
        sprint_match = re.search(r'Sprint\s+(\d+)', event.date, re.IGNORECASE)
        if sprint_match:
            return (1, int(sprint_match.group(1)))
        return (2, event.date)

    seen_events = set()
    unique_timeline = []
    for ev in sorted(timeline_events, key=get_sort_key):
        key = (ev.date, ev.event_description[:60])
        if key not in seen_events:
            seen_events.add(key)
            unique_timeline.append(ev)

    # 3. Group findings, apply multipliers, calculate confidence, sort and pick top 3
    inv_type = ctx.state.get("investigation_type", "")
    if inv_type == "Timeline Reconstruction":
        print("[Investigator] Timeline Reconstruction requested: prioritizing chronological event matching.")
        
    multipliers = {
        "blocker": 1.0,
        "scope_creep": 1.0,
        "resource": 1.0
    }
    
    if inv_type == "Resource Bottlenecks":
        multipliers["resource"] = 2.0
    elif inv_type == "Dependency Analysis":
        multipliers["blocker"] = 2.0
    elif inv_type == "Risk Assessment":
        multipliers["blocker"] = 2.0
        multipliers["scope_creep"] = 2.0
        
    for cat_id, cat_info in categories.items():
        mult = multipliers.get(cat_id, 1.0)
        cat_info["boosted_hits"] = cat_info["hits"] * mult

    contributing_factors = []
    # Sort categories by boosted hits desc
    sorted_cats = sorted(categories.items(), key=lambda x: x[1]["boosted_hits"], reverse=True)
    
    factor_index = 1
    for cat_id, cat_info in sorted_cats:
        if cat_info["hits"] == 0:
            continue
        
        factor_id = f"F{factor_index}"
        factor_index += 1
        confidence = min(round(cat_info["boosted_hits"] / total_chunks, 2), 1.0)
        
        boost_note = " (boosted by investigation type)" if multipliers.get(cat_id, 1.0) > 1.0 else ""
        desc = (
            f"Detected {cat_info['hits']} matching references for {cat_info['name'].lower()} "
            f"patterns (keywords: {', '.join(cat_info['keywords'])}) across project files{boost_note}."
        )
        
        contributing_factors.append(ContributingFactor(
            factor_id=factor_id,
            factor_name=cat_info["name"],
            description=desc,
            confidence=confidence,
            evidence_refs=cat_info["evidence"][:5]  # Top 5 evidence hits
        ))

    # Fallbacks in case queries retrieve no matching keywords
    if not unique_timeline:
        unique_timeline.append(TimelineEvent(
            date="N/A",
            event_description="No timeline milestones or date markers were identified in the project files.",
            source_citation="N/A",
            date_confidence="low"
        ))
    if not contributing_factors:
        contributing_factors.append(ContributingFactor(
            factor_id="F1",
            factor_name="Undetermined Root Cause",
            description="No significant blocker, scope creep, or resource constraints keywords were detected in the project files.",
            confidence=0.10,
            evidence_refs=["Search returned no matching keyword references."]
        ))

    res = InvestigatorOutput(
        timeline=unique_timeline,
        contributing_factors=contributing_factors
    )
    
    ctx.state["investigator_output"] = res.model_dump()
    print(f"[Investigator] Python Investigator dynamically reconstructed {len(res.timeline)} timeline events and {len(res.contributing_factors)} factors.")
    return res

@node(name="run_reporter", rerun_on_resume=True)
async def run_reporter(ctx: Context, node_input: Any) -> FinalReport:
    if ctx.state.get("is_ambiguous", False):
        res = FinalReport(
            report_type="single",
            executive_summary="Your question is ambiguous because it does not specify which project you want to investigate. Please clarify if you are asking about Project Phoenix, Project Apollo, or Project Nebula.",
            timeline=[],
            contributing_factors=[],
            recommendations=[],
            confidence=0.0,
            source_documents=[]
        )
        ctx.state["final_report"] = res.model_dump()
        print("[Reporter] Returned ambiguity report.")
        return res
        
    inv_data = node_input
    if isinstance(inv_data, dict):
        inv_data = InvestigatorOutput(**inv_data)
        
    target = ctx.state.get("target_project", "All")
    is_comparison = False
    if target:
        target_lower = target.lower().strip()
        targets = [t.strip() for t in target.split(",") if t.strip() and t.strip().lower() not in ["all", "ambiguous"]]
        if len(targets) >= 2 or target_lower == "all":
            is_comparison = True
            
    if is_comparison:
        # Map shorthand names to clean titles
        targets_clean = [t.strip().title() for t in target.split(",") if t.strip() and t.strip().lower() not in ["all", "ambiguous"]]
        if not targets_clean:
            targets_clean = ["Project Phoenix", "Project Apollo", "Project Nebula"]
        else:
            mapped = []
            for t in targets_clean:
                if "Phoenix" in t:
                    mapped.append("Project Phoenix")
                elif "Apollo" in t:
                    mapped.append("Project Apollo")
                elif "Nebula" in t:
                    mapped.append("Project Nebula")
                else:
                    mapped.append(t)
            targets_clean = mapped
            
        projects_str = ", ".join(targets_clean)
        json_keys = ", ".join(f'"{p}": "..."' for p in targets_clean)
        
        prompt = (
            f"You are generating a COMPARISON REPORT for the following projects: {projects_str}.\n"
            f"Timeline and factors data:\n{inv_data.model_dump_json() if hasattr(inv_data, 'model_dump_json') else inv_data}\n\n"
            "Please compile the FinalReport. You MUST format and fill the fields exactly as follows:\n"
            "1. Set `report_type` to 'comparison'.\n"
            "2. Set `executive_summary` to a high-level comparison overview of the compared projects (2-3 paragraphs).\n"
            "3. Set `comparison_table` to a list of dicts comparing projects. Each dict MUST only contain keys for 'Metric' and the explicitly compared projects, e.g.:\n"
            "   [\n"
            f"     {{\"Metric\": \"Overall Delay\", {json_keys}}},\n"
            f"     {{\"Metric\": \"Primary Bottleneck\", {json_keys}}},\n"
            f"     {{\"Metric\": \"Biggest Risk\", {json_keys}}},\n"
            f"     {{\"Metric\": \"Major Similarities\", {json_keys}}},\n"
            f"     {{\"Metric\": \"Major Differences\", {json_keys}}}\n"
            "   ]\n"
            "4. Set `shared_vs_unique_issues` to markdown text analyzing:\n"
            "   - ### Common Issues Across Compared Projects\n"
            "   - ### Issues unique to each compared project (only write sub-headers for the projects that are actually compared!)\n"
            "5. Set `comparison_insights` to markdown text containing category-by-category timeline contrast and AI Insights:\n"
            "   - ### Resource Constraints (detailed comparison between projects)\n"
            "   - ### Technical Debt & API Blockers (detailed comparison between projects)\n"
            "   - ### Scope Creep & Requirements Changes (detailed comparison between projects)\n"
            "   - ### AI Insights\n"
            "   - ### Overall Conclusion\n"
            "6. Set `contributing_factors` to the combined contributing factors.\n"
            "7. Set `timeline` to the combined chronological timeline events.\n"
            "8. Set `source_documents` to the list of unique filenames cited in timeline or factors.\n"
            "9. Set `confidence` to overall confidence (0.0 to 1.0).\n"
            "10. Leave `recommendations` empty.\n\n"
            "CRITICAL RULES:\n"
            "- You MUST only include columns and keys in `comparison_table` for the projects that are actually compared. Do NOT include any column or text for projects that are not compared."
        )
    else:
        prompt = (
            f"You are generating a SINGLE PROJECT post-mortem report.\n"
            f"Timeline and factors data:\n{inv_data.model_dump_json() if hasattr(inv_data, 'model_dump_json') else inv_data}\n\n"
            "Please compile the FinalReport. Fill in the following fields:\n"
            "1. Set `report_type` to 'single'.\n"
            "2. Set `executive_summary` to a professional executive summary of the findings (2-3 paragraphs).\n"
            "3. Set `contributing_factors` to the list of contributing factors.\n"
            "4. Set `timeline` to the chronological timeline events.\n"
            "5. Set `source_documents` to all unique source filenames cited in timeline or factors.\n"
            "6. Set `confidence` to overall confidence (0.0 to 1.0).\n"
            "7. Generate specific, actionable recommendations (lessons learned) to prevent these issues in the future. "
            "Each recommendation MUST reference a specific factor ID by setting factor_id (e.g. F1, F2).\n"
            "8. Leave comparison fields (`comparison_table`, `shared_vs_unique_issues`, `comparison_insights`) empty/defaults."
        )
    
    print(f"[Reporter] Running reporter agent (compiling final report)...")
    raw_text = await ctx.run_node(report_agent, node_input=prompt)
    
    response_str = ""
    if isinstance(raw_text, str):
        response_str = raw_text
    elif hasattr(raw_text, "text"):
        response_str = raw_text.text
    elif isinstance(raw_text, dict):
        import json
        response_str = json.dumps(raw_text)
    else:
        response_str = str(raw_text)
        
    cleaned_json = response_str.strip()
    if cleaned_json.startswith("```json"):
        cleaned_json = cleaned_json[7:]
    elif cleaned_json.startswith("```"):
        cleaned_json = cleaned_json[3:]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json[:-3]
    cleaned_json = cleaned_json.strip()
    
    import json
    try:
        report_data = json.loads(cleaned_json)
    except Exception as e:
        print(f"[Reporter] JSON parsing failed: {e}. Attempting leniency substring extraction.")
        start = cleaned_json.find("{")
        end = cleaned_json.rfind("}")
        if start != -1 and end != -1:
            try:
                report_data = json.loads(cleaned_json[start : end + 1])
            except Exception as inner_e:
                print(f"[Reporter] Substring JSON parse also failed: {inner_e}")
                report_data = {
                    "report_type": "single" if not is_comparison else "comparison",
                    "executive_summary": "Error: Failed to parse report JSON from agent response.",
                    "contributing_factors": [],
                    "timeline": [],
                    "source_documents": [],
                    "confidence": 0.0
                }
        else:
            report_data = {
                "report_type": "single" if not is_comparison else "comparison",
                "executive_summary": f"Error: No JSON object found in response. Raw response: {response_str[:500]}",
                "contributing_factors": [],
                "timeline": [],
                "source_documents": [],
                "confidence": 0.0
            }
            
    res = FinalReport(**report_data)
    ctx.state["final_report"] = res.model_dump()
    print("[Reporter] Final report parsed and validated successfully.")
    return res

# 3. Connect Workflow Edges (Strictly 2 Gemini calls, sequential logic)
edges = [
    Edge(from_node=START, to_node=run_planner),
    Edge(from_node=run_planner, to_node=retriever_node),
    Edge(from_node=retriever_node, to_node=run_investigator),
    Edge(from_node=run_investigator, to_node=run_reporter)
]

workflow = Workflow(name="project_intelligence_workflow", edges=edges)
