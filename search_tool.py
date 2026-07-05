import re
from google.adk.tools import ToolContext

def search_project_documents(query: str, ctx: ToolContext) -> str:
    """Search the uploaded project artifacts (Jira, Slack, notes) for relevant information.
    
    Args:
        query: The search term, keyword, or sentence describing what to look for.
    """
    chunks = ctx.state.get("file_chunks", [])
    if not chunks:
        return "No documents uploaded or parsed yet."

    # Parse query into keywords
    keywords = [w.lower() for w in re.findall(r'\b\w{3,}\b', query)]
    # Stop words to exclude
    stop_words = {"why", "was", "did", "the", "and", "for", "project", "delayed", "delay", "blocker", "bottleneck", "sprint"}
    keywords = [w for w in keywords if w not in stop_words]

    if not keywords:
        # Fallback to simple split if query is very short or all words are stop words
        keywords = [w.lower() for w in query.split() if w.strip()]

    scored_chunks = []
    for chunk in chunks:
        content = chunk.get("content", "").lower()
        score = 0
        
        # Keyword matching
        for keyword in keywords:
            count = content.count(keyword)
            score += count * 2.0  # Add 2 points per match
            
            # Give extra points if the keyword matches the source filename
            if keyword in chunk.get("source", "").lower():
                score += 5.0
        
        # Phrase match: if the full query or parts of it appear verbatim
        phrase_len = len(query.strip())
        if phrase_len > 4 and query.strip().lower() in content:
            score += 20.0
            
        # Give extra weight if the chunk mentions "blocked", "delay", "bottleneck", "sick", "scope"
        for critical_word in ["blocked", "delay", "bottleneck", "sick", "leave", "scope", "creep", "api", "dependency"]:
            if critical_word in content:
                score += 3.0

        if score > 0:
            scored_chunks.append((score, chunk))

    # Sort by score desc
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Take top 15 chunks
    top_chunks = scored_chunks[:15]
    if not top_chunks:
        return "No matching evidence found in the documents."

    formatted_results = []
    for score, chunk in top_chunks:
        formatted_results.append(
            f"--- EVIDENCE CHUNK (Relevance Score: {score:.1f}) ---\n"
            f"Source: {chunk['source']}\n"
            f"Location: {chunk['location']}\n"
            f"Date: {chunk.get('date', 'N/A')}\n"
            f"Content:\n{chunk['content']}\n"
        )
        
    return "\n".join(formatted_results)
