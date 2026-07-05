import os
import re
import pandas as pd
import fitz  # PyMuPDF

def load_pdf(filepath: str) -> list[dict]:
    """Extract text from a PDF file page by page with metadata."""
    chunks = []
    filename = os.path.basename(filepath)
    try:
        doc = fitz.open(filepath)
        for page_idx, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                continue
            
            # Try to find a date in the page text (e.g. YYYY-MM-DD)
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)
            date_str = date_match.group(0) if date_match else ""
            
            chunks.append({
                "source": filename,
                "content": f"[PDF Document: {filename} - Page {page_idx + 1}]\n{text.strip()}",
                "location": f"page {page_idx + 1}",
                "date": date_str
            })
    except Exception as e:
        print(f"Error loading PDF {filepath}: {e}")
    return chunks

def load_csv(filepath: str) -> list[dict]:
    """Load a CSV and group tickets by Sprint to minimize chunk count and token usage."""
    chunks = []
    filename = os.path.basename(filepath)
    try:
        df = pd.read_csv(filepath)
        df = df.fillna("")
        
        # Check if Sprint column is present
        sprint_col = None
        for col in df.columns:
            if col.lower() == 'sprint':
                sprint_col = col
                break
                
        if sprint_col and len(df) > 0:
            # Group by Sprint values
            grouped = df.groupby(sprint_col)
            for sprint_name, group_df in grouped:
                sprint_str = str(sprint_name).strip()
                if not sprint_str:
                    sprint_str = "Unassigned Sprint"
                    
                ticket_details = []
                for idx, row in group_df.iterrows():
                    key = row.get("Issue key", row.get("Issue Key", f"Row-{idx+1}"))
                    summary = row.get("Summary", "")
                    status = row.get("Status", "")
                    priority = row.get("Priority", "")
                    desc = row.get("Description", "")
                    # Limit description size to minimize context window token usage
                    short_desc = desc[:80] + "..." if len(desc) > 80 else desc
                    ticket_details.append(
                        f"- Ticket {key}: {summary} | Status: {status} | Priority: {priority} | Desc: {short_desc}"
                    )
                
                content = f"[Jira Tickets Summary for {sprint_str} in {filename}]\n" + "\n".join(ticket_details)
                chunks.append({
                    "source": filename,
                    "content": content,
                    "location": f"Sprint: {sprint_str}",
                    "date": ""  # Dates can be extracted by downstream timeline parser
                })
        else:
            # Fallback to row-level chunking with description limiting if no Sprint column
            for idx, row in df.iterrows():
                row_items = []
                for col in df.columns:
                    val = str(row[col]).strip()
                    if not val:
                        continue
                    if len(val) > 80:
                        val = val[:80] + "..."
                    row_items.append(f"{col}: {val}")
                content = f"[Jira Row {idx + 1} in {filename}]\n" + " | ".join(row_items)
                chunks.append({
                    "source": filename,
                    "content": content,
                    "location": f"row {idx + 1}",
                    "date": ""
                })
    except Exception as e:
        print(f"Error loading CSV {filepath}: {e}")
    return chunks

def load_txt(filepath: str) -> list[dict]:
    """Load a text file and chunk it by paragraph blocks to reduce chunk count."""
    chunks = []
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
            
        if not content:
            return chunks
            
        # Group Slack messages by block, or generic text by paragraph blocks
        is_slack = "slack" in filename.lower()
        
        if is_slack:
            # Slack chat can be kept as a single unified chunk for small logs to preserve context
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', content)
            date_str = date_match.group(0) if date_match else ""
            chunks.append({
                "source": filename,
                "content": f"[Slack Chat Log: {filename}]\n{content}",
                "location": "complete log",
                "date": date_str
            })
        else:
            # Generic text split by double newlines (paragraphs)
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for idx, para in enumerate(paragraphs):
                date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', para)
                date_str = date_match.group(0) if date_match else ""
                chunks.append({
                    "source": filename,
                    "content": f"[Text Document: {filename} - Section {idx + 1}]\n{para}",
                    "location": f"section {idx + 1}",
                    "date": date_str
                })
    except Exception as e:
        print(f"Error loading TXT {filepath}: {e}")
    return chunks

def chunk_documents(filepaths: list[str]) -> list[dict]:
    """Inferred chunking of documents based on file extensions."""
    all_chunks = []
    for filepath in filepaths:
        if not os.path.exists(filepath):
            continue
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            all_chunks.extend(load_pdf(filepath))
        elif ext == '.csv':
            all_chunks.extend(load_csv(filepath))
        elif ext in ['.txt', '.log']:
            all_chunks.extend(load_txt(filepath))
        else:
            all_chunks.extend(load_txt(filepath))
    return all_chunks
