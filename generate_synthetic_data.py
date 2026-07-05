import os
import csv
import fitz  # PyMuPDF to create PDF

def create_synthetic_data():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Clean up old non-prefixed files if they exist to avoid confusion
    old_files = ["jira_export.csv", "sprint2_retrospective.pdf", "sprint4_retrospective.pdf", "slack_export.txt", "project_timeline.txt"]
    for f in old_files:
        old_path = os.path.join(data_dir, f)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    # ==================== 1. PROJECT PHOENIX ====================
    print("Generating Project Phoenix dataset...")
    
    # Jira CSV
    phoenix_csv = os.path.join(data_dir, "phoenix_jira_export.csv")
    csv_headers = ["Issue key", "Summary", "Description", "Status", "Priority", "Created", "Updated", "Sprint", "Assignee"]
    tickets = []
    for i in range(1, 11):
        tickets.append([f"PHX-{100+i}", f"Set up database schema part {i}", f"Define database models and relationships for module {i}", "Done", "Medium", "2026-04-02 09:00:00", "2026-04-10 17:00:00", "Sprint 1", "Developer A"])
    for i in range(11, 21):
        tickets.append([f"PHX-{100+i}", f"Implement user authentication subtask {i-10}", f"Build secure login, token validation, and password reset flows.", "Done", "High", "2026-04-16 10:00:00", "2026-04-28 18:00:00", "Sprint 2", "Developer B"])
    tickets.append(["PHX-121", "ADDITIONAL FEATURE: Social login options (Google & GitHub)", "Stakeholders requested social auth integrations immediately. Adding to Sprint 2 scope.", "Done", "High", "2026-04-20 11:30:00", "2026-04-29 16:00:00", "Sprint 2", "Developer B"])
    tickets.append(["PHX-122", "ADDITIONAL FEATURE: MFA Authenticator support", "Added mid-sprint. Integrate Google Authenticator TOTP flow.", "In Progress", "Critical", "2026-04-22 14:00:00", "2026-04-30 18:00:00", "Sprint 2", "Developer A"])
    for i in range(23, 35):
        tickets.append([f"PHX-{100+i}", f"Billing integration task {i-22}", f"Connect third-party billing gateway to process payments.", "Done" if i != 25 else "Blocked", "High", "2026-05-02 09:00:00", "2026-05-14 17:00:00", "Sprint 3", "Developer C"])
    tickets.append(["PHX-135", "BLOCKED: Payment API token gateway credentials", "Unable to test payment endpoints. Third-party billing provider hasn't updated their auth protocol for our region. Awaiting vendor response.", "Blocked", "Critical", "2026-05-05 10:00:00", "2026-05-24 12:00:00", "Sprint 3", "Developer C"])
    for i in range(36, 48):
        tickets.append([f"PHX-{100+i}", f"Analytics dashboard panel {i-35}", f"Build visualization widgets for data analytics.", "Done" if i < 43 else "In Progress", "Medium", "2026-05-16 09:00:00", "2026-05-28 17:00:00", "Sprint 4", "Developer D"])
    tickets.append(["PHX-149", "UNFINISHED: Final dashboard visual graphs", "Dashboard graphs delayed due to resources out sick. 10 man-days lost in frontend team.", "In Progress", "High", "2026-05-22 09:00:00", "2026-05-28 18:00:00", "Sprint 4", "Developer E"])
    
    with open(phoenix_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        writer.writerows(tickets)

    # PDFs
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "PROJECT PHOENIX - SPRINT 2 RETROSPECTIVE NOTES\nDate: 2026-04-30\n\n"
        "What Went Well:\n- Database schemas are stable.\n- Basic auth is implemented.\n\n"
        "What Didn't Go Well:\n- Scope Creep: We added social login and MFA support mid-sprint. This expanded the sprint scope by 35%.\n"
        "- The authentication tasks took longer than expected because of the added requirements.\n"
        "- Developer B worked overtime to complete the social logins but MFA is still in progress.\n\n"
        "Action Items:\n- Lock scope at the beginning of the sprint.\n- Reject mid-sprint change requests."
    )
    page.insert_text((50, 72), text, fontsize=11)
    doc.save(os.path.join(data_dir, "phoenix_sprint2_retrospective.pdf"))
    doc.close()

    doc = fitz.open()
    page = doc.new_page()
    text = (
        "PROJECT PHOENIX - SPRINT 4 RETROSPECTIVE NOTES\nDate: 2026-05-28\n\n"
        "What Went Well:\n- Payments gateway was successfully integrated after the vendor API issue resolved in Sprint 3.\n\n"
        "What Didn't Go Well:\n- Resource Constraints: Developer D and Developer E (our core frontend engineers) fell down with severe flu during the second week of the sprint.\n"
        "- This resulted in a total of 10 man-days lost.\n"
        "- The analytics dashboard panels and graph widgets could not be completed on time.\n"
        "- The final release of Project Phoenix is delayed by 6 weeks cumulative (2 weeks from Sprint 3 API blocker + 4 weeks from Sprint 4 resource shortage).\n\n"
        "Action Items:\n- Build a cross-training plan so backend developers can assist with frontend tasks.\n- Schedule buffer days."
    )
    page.insert_text((50, 72), text, fontsize=11)
    doc.save(os.path.join(data_dir, "phoenix_sprint4_retrospective.pdf"))
    doc.close()

    # Slack TXT
    with open(os.path.join(data_dir, "phoenix_slack_export.txt"), "w", encoding="utf-8") as f:
        f.write(
            "[2026-05-05 10:12:00] Alice (Product Manager): Team, we have a billing integration task. Developer C, how is PHX-135 going?\n"
            "[2026-05-05 10:15:30] Developer C: I'm blocked. The billing API response is returning auth signature errors. Their gateway updated credentials rules but our test environment config is rejected.\n"
            "[2026-05-05 10:18:22] Developer C: Filed a high-priority ticket. They said it's a known issue for regional accounts, dev team is fixing it, but ETA is 2 weeks.\n"
            "[2026-05-12 09:15:00] Developer C: Still blocked. We cannot test payments. The entire Sprint 3 milestone is slipping because of this API blocker.\n"
            "[2026-05-20 10:00:00] Developer C: Good news, the billing vendor API issue is resolved. I've successfully connected and tested the gateway. PHX-135 is closed. Delay was exactly 15 days.\n"
            "[2026-05-22 09:30:00] Developer D: Hey Alice, just letting you know I've tested positive for flu. I'm feeling awful and won't be able to work this week.\n"
            "[2026-05-22 09:35:00] Developer E: Bad timing, I am also down with high fever. Doctor says I need complete bed rest for at least 5 days. Sorry team.\n"
            "[2026-05-22 09:40:00] Bob (Engineering Lead): That is both our frontend guys out. That leaves the dashboard team completely empty for week 2. 10 man-days lost.\n"
            "[2026-05-22 09:42:00] Alice: Okay, we will have to explain this delay to the steering committee. The release is slipping.\n"
        )

    # Timeline TXT
    with open(os.path.join(data_dir, "phoenix_project_timeline.txt"), "w", encoding="utf-8") as f:
        f.write(
            "PROJECT PHOENIX MILESTONES TIMELINE\n------------------------------------\n"
            "Sprint 1 (Database & Setup):\n  Planned: 2026-04-01 to 2026-04-14\n  Actual: 2026-04-01 to 2026-04-14\n  Status: Completed on time.\n\n"
            "Sprint 2 (Authentication & Scope Creep):\n  Planned: 2026-04-15 to 2026-04-28\n  Actual: 2026-04-15 to 2026-05-02\n  Status: Completed with 4 days delay due to social login/MFA scope creep.\n\n"
            "Sprint 3 (Billing Gateway & API Blocker):\n  Planned: 2026-04-29 to 2026-05-12\n  Actual: 2026-04-29 to 2026-05-24\n  Status: Completed with 12 days delay due to external payment API billing credentials gateway blocker.\n\n"
            "Sprint 4 (Dashboard & Resource Outage):\n  Planned: 2026-05-13 to 2026-05-26\n  Actual: 2026-05-13 to 2026-07-09\n  Status: Delayed by 6 weeks total. Developer D and Developer E fell down with flu in week 2, losing 10 man-days. Dashboard unfinished.\n"
        )


    # ==================== 2. PROJECT APOLLO ====================
    print("Generating Project Apollo dataset (Technical Debt & Outages)...")
    
    # Jira CSV
    apollo_csv = os.path.join(data_dir, "apollo_jira_export.csv")
    tickets = []
    for i in range(1, 11):
        tickets.append([f"APL-{100+i}", f"Set up database schema part {i}", f"Legacy database setup tasks.", "Done", "Medium", "2026-04-02 09:00:00", "2026-04-10 17:00:00", "Sprint 1", "Developer A"])
    for i in range(11, 21):
        tickets.append([f"APL-{100+i}", f"ORM legacy migration subtask {i-10}", f"Migrate backend tables to LEGACY structure.", "Done" if i != 15 else "Blocked", "High", "2026-04-16 10:00:00", "2026-04-28 18:00:00", "Sprint 2", "Developer B"])
    tickets.append(["APL-121", "BLOCKED: LEGACY ORM dependency upgrade issues", "obsolete database library connector is deprecated. We are blocked by legacy libraries dependency errors.", "Blocked", "High", "2026-04-20 11:30:00", "2026-04-29 16:00:00", "Sprint 2", "Developer B"])
    for i in range(23, 35):
        tickets.append([f"APL-{100+i}", f"Cloud deployment test {i-22}", f"Deploy regional nodes to production.", "Done" if i != 25 else "Blocked", "High", "2026-05-02 09:00:00", "2026-05-14 17:00:00", "Sprint 3", "Developer C"])
    tickets.append(["APL-135", "BLOCKED: Regional cloud gateway provider blackout", "Deployment server is blocked due to the cloud provider outage, on hold for 8 days.", "Blocked", "Critical", "2026-05-05 10:00:00", "2026-05-24 12:00:00", "Sprint 3", "Developer C"])
    for i in range(36, 48):
        tickets.append([f"APL-{100+i}", f"Analytics module {i-35}", f"Setup dashboard visuals.", "Done" if i < 43 else "In Progress", "Medium", "2026-05-16 09:00:00", "2026-05-28 17:00:00", "Sprint 4", "Developer D"])
    tickets.append(["APL-149", "UNFINISHED: Resolving database technical debt fallout", "Obsolete connectors and waiting for legacy schema dependency migrations.", "In Progress", "High", "2026-05-22 09:00:00", "2026-05-28 18:00:00", "Sprint 4", "Developer E"])
    
    with open(apollo_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        writer.writerows(tickets)

    # PDFs
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "PROJECT APOLLO - SPRINT 2 RETROSPECTIVE NOTES\nDate: 2026-04-30\n\n"
        "What Went Well:\n- Database connections are initialized.\n\n"
        "What Didn't Go Well:\n- Technical Debt: We are blocked by legacy ORM database migration. The dependency conflicts are severe, causing 5 days delay.\n"
        "- Obsolete legacy ORM connector libraries are causing database conflicts.\n"
        "- Waiting for legacy schema fixes took 5 days.\n\n"
        "Action Items:\n- Refactor legacy database libraries.\n- Allocate budget for technical debt."
    )
    page.insert_text((50, 72), text, fontsize=11)
    doc.save(os.path.join(data_dir, "apollo_sprint2_retrospective.pdf"))
    doc.close()

    doc = fitz.open()
    page = doc.new_page()
    text = (
        "PROJECT APOLLO - SPRINT 4 RETROSPECTIVE NOTES\nDate: 2026-05-28\n\n"
        "What Went Well:\n- Legacy system was patched.\n\n"
        "What Didn't Go Well:\n- Infrastructure Outages: Major cloud provider outage in regional server zone, leaving API servers offline.\n"
        "- Entire regional server deployment was delayed due to data center server blackout.\n"
        "- Cumulative project delays have reached 4 weeks due to severe technical debt blockers and regional infrastructure outages.\n\n"
        "Action Items:\n- Setup secondary failover cloud provider.\n- Address legacy code dependency debt."
    )
    page.insert_text((50, 72), text, fontsize=11)
    doc.save(os.path.join(data_dir, "apollo_sprint4_retrospective.pdf"))
    doc.close()

    # Slack TXT
    with open(os.path.join(data_dir, "apollo_slack_export.txt"), "w", encoding="utf-8") as f:
        f.write(
            "[2026-04-20 10:00:00] Developer A: I am blocked. Legacy ORM database connector is deprecated and waiting for resolution.\n"
            "[2026-04-22 14:15:00] Developer A: Dependency conflicts are severe. Technical debt is catching up with us.\n"
            "[2026-05-05 10:15:30] Developer B: The deployment server is blocked due to the cloud provider outage, on hold for 8 days.\n"
            "[2026-05-12 09:15:00] Developer B: Regional server went dark. Waiting for cloud provider to recover from regional outage grid blackout.\n"
            "[2026-05-22 09:30:00] Developer C: Deprecated library build dependency is blocked. We are waiting for upgrades.\n"
        )

    # Timeline TXT
    with open(os.path.join(data_dir, "apollo_project_timeline.txt"), "w", encoding="utf-8") as f:
        f.write(
            "PROJECT APOLLO MILESTONES TIMELINE\n------------------------------------\n"
            "Sprint 1 (Setup):\n  Planned: 2026-04-01 to 2026-04-14\n  Actual: 2026-04-01 to 2026-04-14\n  Status: Completed on time.\n\n"
            "Sprint 2 (Legacy Migration & Technical Debt):\n  Planned: 2026-04-15 to 2026-04-28\n  Actual: 2026-04-15 to 2026-05-03\n  Status: Completed with 5 days delay due to obsolete legacy ORM libraries database blocker and technical debt.\n\n"
            "Sprint 3 (Regional Cloud & Infrastructure Outage):\n  Planned: 2026-04-29 to 2026-05-12\n  Actual: 2026-04-29 to 2026-05-21\n  Status: Completed with 9 days delay due to cloud infrastructure outage and data center server blackout.\n\n"
            "Sprint 4 (Dashboard & Legacy Debt):\n  Planned: 2026-05-13 to 2026-05-26\n  Actual: 2026-05-13 to 2026-06-10\n  Status: Delayed by 4 weeks total due to database dependency conflicts, legacy libraries ORM errors, and cloud outages.\n"
        )


    # ==================== 3. PROJECT NEBULA ====================
    print("Generating Project Nebula dataset (Requirements & Scope Creep)...")
    
    # Jira CSV
    nebula_csv = os.path.join(data_dir, "nebula_jira_export.csv")
    tickets = []
    for i in range(1, 11):
        tickets.append([f"NEB-{100+i}", f"Set up checkout module part {i}", f"Core checkout page layout.", "Done", "Medium", "2026-04-02 09:00:00", "2026-04-10 17:00:00", "Sprint 1", "Developer A"])
    for i in range(11, 21):
        tickets.append([f"NEB-{100+i}", f"Checkout subtask {i-10}", f"Process payments in multiple formats.", "Done", "High", "2026-04-16 10:00:00", "2026-04-28 18:00:00", "Sprint 2", "Developer B"])
    tickets.append(["NEB-121", "ADDITIONAL FEATURE: Dynamic tax calculation", "Client requested checkout redesign with dynamic pricing. Added mid-sprint.", "Done", "High", "2026-04-20 11:30:00", "2026-04-29 16:00:00", "Sprint 2", "Developer B"])
    tickets.append(["NEB-122", "ADDITIONAL FEATURE: Multi-currency coupon conversions", "Added mid-sprint. Integrate multi-currency. Client scope change.", "In Progress", "Critical", "2026-04-22 14:00:00", "2026-04-30 18:00:00", "Sprint 2", "Developer A"])
    for i in range(23, 35):
        tickets.append([f"NEB-{100+i}", f"API connector {i-22}", f"Connect to vendor API.", "Done" if i != 25 else "Blocked", "High", "2026-05-02 09:00:00", "2026-05-14 17:00:00", "Sprint 3", "Developer C"])
    tickets.append(["NEB-135", "BLOCKED: Payment vendor API credentials auth protocol update", "Vendor updated payment API protocol without notice. We are blocked and waiting for documentation.", "Blocked", "Critical", "2026-05-05 10:00:00", "2026-05-24 12:00:00", "Sprint 3", "Developer C"])
    for i in range(36, 48):
        tickets.append([f"NEB-{100+i}", f"Dashboard graph {i-35}", f"Design visuals.", "Done" if i < 43 else "In Progress", "Medium", "2026-05-16 09:00:00", "2026-05-28 17:00:00", "Sprint 4", "Developer D"])
    tickets.append(["NEB-149", "UNFINISHED: Short-staffed dashboard panels", "Team underresourced. Two developers reassigned. Unavailable, on leave for Project X.", "In Progress", "High", "2026-05-22 09:00:00", "2026-05-28 18:00:00", "Sprint 4", "Developer E"])
    
    with open(nebula_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        writer.writerows(tickets)

    # PDFs
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "PROJECT NEBULA - SPRINT 2 RETROSPECTIVE NOTES\nDate: 2026-04-30\n\n"
        "What Went Well:\n- Checkout design is stable.\n\n"
        "What Didn't Go Well:\n- Scope Creep: Client requested checkout redesign with dynamic tax, pricing, and multi-currency conversions.\n"
        "- This mid-sprint scope change added 35% scope expansion.\n"
        "- Additional requirements caused Sprint 2 checkout task delays of 6 days.\n\n"
        "Action Items:\n- Minimize mid-sprint client requirement changes.\n- Enforce scope lock."
    )
    page.insert_text((50, 72), text, fontsize=11)
    doc.save(os.path.join(data_dir, "nebula_sprint2_retrospective.pdf"))
    doc.close()

    doc = fitz.open()
    page = doc.new_page()
    text = (
        "PROJECT NEBULA - SPRINT 4 RETROSPECTIVE NOTES\nDate: 2026-05-28\n\n"
        "What Went Well:\n- Payment vendor credentials updated successfully.\n\n"
        "What Didn't Go Well:\n- Resource Constraints: Team was short-staffed because two developers were pulled to assist another critical project, leaving us underresourced.\n"
        "- Having 2 core devs unavailable and on leave resulted in 12 developer-days lost.\n"
        "- The project release is delayed by 5 weeks cumulative due to scope creep, payment vendor API blockers, and being short-staffed.\n\n"
        "Action Items:\n- Prevent pulling team resources mid-project.\n- Cross-train fallback engineers."
    )
    page.insert_text((50, 72), text, fontsize=11)
    doc.save(os.path.join(data_dir, "nebula_sprint4_retrospective.pdf"))
    doc.close()

    # Slack TXT
    with open(os.path.join(data_dir, "nebula_slack_export.txt"), "w", encoding="utf-8") as f:
        f.write(
            "[2026-04-20 10:00:00] Alice (PM): Client requested a checkout redesign with dynamic pricing. Developer A: That's out of scope.\n"
            "[2026-04-20 10:15:00] Alice: It is an additional client requirement, so we must add it.\n"
            "[2026-05-05 10:15:30] Developer B: Payment API integration is blocked by updated auth credentials protocol. We are waiting for vendor documentation.\n"
            "[2026-05-12 09:15:00] Developer B: Payment gateway is still blocked. Vendor did not notify us of protocol auth changes.\n"
            "[2026-05-22 09:30:00] Developer C: We are short-staffed this sprint because Developer D and E are unavailable, on leave for Project X.\n"
            "[2026-05-22 09:40:00] Bob: That leaves dashboard team underresourced. 12 man-days lost.\n"
        )

    # Timeline TXT
    with open(os.path.join(data_dir, "nebula_project_timeline.txt"), "w", encoding="utf-8") as f:
        f.write(
            "PROJECT NEBULA MILESTONES TIMELINE\n------------------------------------\n"
            "Sprint 1 (Setup):\n  Planned: 2026-04-01 to 2026-04-14\n  Actual: 2026-04-01 to 2026-04-14\n  Status: Completed on time.\n\n"
            "Sprint 2 (Checkout & Client Scope Creep):\n  Planned: 2026-04-15 to 2026-04-28\n  Actual: 2026-04-15 to 2026-05-04\n  Status: Completed with 6 days delay due to scope change client requirements.\n\n"
            "Sprint 3 (Payment Gateway Vendor API Block):\n  Planned: 2026-04-29 to 2026-05-12\n  Actual: 2026-04-29 to 2026-05-19\n  Status: Completed with 7 days delay due to external payment API dependency blocker.\n\n"
            "Sprint 4 (Dashboard & Resource Short-staffed):\n  Planned: 2026-05-13 to 2026-05-26\n  Actual: 2026-05-13 to 2026-06-17\n  Status: Delayed by 5 weeks total. Team was short-staffed and underresourced due to developer leaves.\n"
        )

    print("All 3 software project datasets generated successfully in data/ directory!")

if __name__ == "__main__":
    create_synthetic_data()
