import sys
import os

print("--- TESTING CODE COMPILATION AND DATA INGESTION ---")

try:
    # Test importing models
    import models
    print("[OK] Models imported successfully.")
except Exception as e:
    print("[ERROR] Failed to import models:", e)
    sys.exit(1)

try:
    # Test importing document_loader
    import document_loader
    print("[OK] Document loader imported successfully.")
    
    # Test chunking of synthetic data
    demo_files = [
        os.path.join("data", "phoenix_jira_export.csv"),
        os.path.join("data", "phoenix_sprint2_retrospective.pdf"),
        os.path.join("data", "phoenix_sprint4_retrospective.pdf"),
        os.path.join("data", "phoenix_slack_export.txt"),
        os.path.join("data", "phoenix_project_timeline.txt")
    ]
    chunks = document_loader.chunk_documents(demo_files)
    print(f"[OK] Chunking successful: Generated {len(chunks)} chunks from synthetic dataset.")
    if len(chunks) > 0:
        print(f"   Sample chunk keys: {list(chunks[0].keys())}")
        print(f"   Sample chunk source: {chunks[0]['source']}")
except Exception as e:
    print("[ERROR] Failed to test document loading/chunking:", e)
    sys.exit(1)

try:
    # Test importing search_tool
    import search_tool
    print("[OK] Search tool imported successfully.")
except Exception as e:
    print("[ERROR] Failed to import search_tool:", e)
    sys.exit(1)

try:
    # Test importing agents_workflow and building graph
    import agents_workflow
    print("[OK] Agents workflow imported successfully.")
    
    graph = agents_workflow.workflow._build_graph()
    print("[OK] Graph constructed and validated successfully.")
    print("   Graph nodes in pipeline:", [node.name for node in graph.nodes])
except Exception as e:
    print("[ERROR] Failed to build or validate agents workflow:", e)
    sys.exit(1)

print("\nALL LOCAL COMPILATION AND DATAPATH VERIFICATIONS COMPLETED SUCCESSFULLY!")
