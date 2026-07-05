from pydantic import BaseModel, Field
from typing import List, Literal

class PlannerOutput(BaseModel):
    """Output schema for the Planner Agent's retrieval strategy."""
    question_type: str = Field(description="The categorized type of the question, e.g. 'delay_analysis', 'bottleneck_identification', 'lessons_learned'.")
    evidence_needed: List[str] = Field(description="A list describing what types of evidence are needed.")
    search_queries: List[str] = Field(description="A list of target search queries to run against project documents.")
    target_project: str = Field(default="All", description="The name of the project targeted by the user query, e.g. 'Phoenix', 'Apollo', 'Nebula', or 'All'.")

class TimelineEvent(BaseModel):
    """Represents a single event in the project timeline."""
    date: str = Field(description="The date or date range of the event (e.g. '2026-04-12' or 'Sprint 2').")
    event_description: str = Field(description="Description of what happened.")
    source_citation: str = Field(description="Source file name and section/page (e.g. 'slack_export.txt:line 45').")
    date_confidence: Literal["high", "medium", "low"] = Field(description="Confidence in the accuracy of the date/timeline placement.")

class ContributingFactor(BaseModel):
    """Represents a contributing factor to the project delay/blocker."""
    factor_id: str = Field(description="A short unique ID for this factor, e.g. 'F1', 'F2'.")
    factor_name: str = Field(description="Name of the contributing factor.")
    description: str = Field(description="Detailed explanation of the factor and how it caused the bottleneck/delay.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0 for this factor.")
    evidence_refs: List[str] = Field(description="Supporting quotes and source citations from the documents.")

class InvestigatorOutput(BaseModel):
    """Output schema for the Investigator Agent (merging Timeline and Factor Analysis)."""
    timeline: List[TimelineEvent] = Field(description="Chronological events reconstructed from the evidence.")
    contributing_factors: List[ContributingFactor] = Field(description="Key contributing factors with confidence scores and citations.")

class Recommendation(BaseModel):
    """Represents an actionable recommendation tied to a contributing factor."""
    recommendation_id: str = Field(description="Unique ID for this recommendation, e.g. 'R1', 'R2'.")
    factor_id: str = Field(description="The ID of the contributing factor this recommendation addresses (must match a factor_id).")
    suggested_action: str = Field(description="Actionable suggestion or lesson learned to prevent this in the future.")

class ReporterOutput(BaseModel):
    """Output schema for the Reporter Agent (merging Recommendations and Summary)."""
    summary: str = Field(description="A professional executive summary of the post-mortem findings (2-3 paragraphs).")
    recommendations: List[Recommendation] = Field(description="List of recommendations tied to specific contributing factors.")
    overall_confidence: float = Field(description="Overall confidence score for the analysis (0.0 to 1.0).")

class FinalReport(BaseModel):
    """The compiled final post-mortem report schema."""
    report_type: Literal["single", "comparison"] = Field(description="The type of report: 'single' for one project, 'comparison' for comparing multiple projects.")
    executive_summary: str = Field(description="Executive summary overview of what happened and why (or comparison overview for multiple projects).")
    contributing_factors: List[ContributingFactor] = Field(description="List of contributing factors identified.")
    timeline: List[TimelineEvent] = Field(description="Chronological timeline events reconstructed.")
    source_documents: List[str] = Field(description="All unique source files cited in the report.")
    confidence: float = Field(description="Overall confidence score for the analysis (0.0 to 1.0).")
    
    # Comparison-only fields
    comparison_table: List[dict] = Field(
        default=[],
        description="Tabular comparison of metrics across projects, e.g. [{'Metric': 'Overall Delay', 'Project Phoenix': '6 weeks', 'Project Nebula': '5 weeks'}, ...]."
    )
    shared_vs_unique_issues: str = Field(
        default="",
        description="Markdown text comparing common root causes and project-specific issues."
    )
    comparison_insights: str = Field(
        default="",
        description="Markdown category-by-category timeline contrast and AI insights explaining process differences."
    )
    
    # Single-only fields
    recommendations: List[Recommendation] = Field(
        default=[],
        description="Actionable recommendations tied to contributing factors."
    )
