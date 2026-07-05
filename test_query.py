import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from document_loader import chunk_documents
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents_workflow import workflow
from models import FinalReport

async def run_test():
    # Load synthetic files
    files = [
        os.path.join("data", "phoenix_jira_export.csv"),
        os.path.join("data", "phoenix_sprint2_retrospective.pdf"),
        os.path.join("data", "phoenix_sprint4_retrospective.pdf"),
        os.path.join("data", "phoenix_slack_export.txt"),
        os.path.join("data", "phoenix_project_timeline.txt")
    ]
    chunks = chunk_documents(files)
    print(f"Chunks parsed: {len(chunks)}")
    
    session_service = InMemorySessionService()
    runner = Runner(session_service=session_service, node=workflow, auto_create_session=True)
    
    query = "Why was Project Phoenix delayed 6 weeks?"
    msg = types.Content(role="user", parts=[types.Part(text=query)])
    
    state_delta = {
        "file_chunks": chunks,
        "uploaded_files": [os.path.basename(f) for f in files],
        "user_question": query
    }
    
    print("Starting runner.run_async...")
    try:
        async for event in runner.run_async(
            user_id="test_user",
            session_id="session_1",
            new_message=msg,
            state_delta=state_delta
        ):
            # Extract node name from path
            node_name = ""
            if event.node_info and event.node_info.path:
                parts = event.node_info.path.split('/')
                if len(parts) > 1:
                    node_name = parts[-1].split('@')[0]
            if not node_name:
                node_name = event.author or ""
                
            print(f"\n--- EVENT: node={node_name} author={event.author} ---")
            if event.output is not None:
                print(f"Output type: {type(event.output)}")
                print(f"Output preview: {str(event.output)[:200]}")
            if event.error_message:
                print(f"ERROR: {event.error_message}")
    except Exception as e:
        import traceback
        print("\n[ERROR] PIPELINE FAILED WITH EXCEPTION:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
