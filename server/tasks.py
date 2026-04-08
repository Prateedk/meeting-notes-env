"""Task definitions for Meeting Notes → Action Items environment.

32 tasks across 3 difficulty levels:
  - Easy (10):  Short transcripts, 1 action item, explicit assignment
  - Medium (10): Multi-speaker, 3-4 action items, clear but spread across dialogue
  - Hard (12):  Long transcripts, implicit owners, vague deadlines, red herrings,
                superseded decisions, cross-references, negated actions
"""

from __future__ import annotations
from typing import Any, Dict

TASKS: Dict[str, Dict[str, Any]] = {

    # =====================================================================
    # EASY — 1 action item, short transcript, explicit who/what/when
    # =====================================================================

    "easy_1": {
        "difficulty": "easy",
        "description": "Extract the single action item from a short standup.",
        "transcript": (
            "Team standup — 9 AM Monday\n"
            "Alice: The deployment scripts are broken again. "
            "Bob, can you fix the CI pipeline by end of day Wednesday?\n"
            "Bob: Sure, I'll get on it.\n"
            "Alice: Great. Nothing else for today."
        ),
        "ground_truth": [
            {"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}
        ],
    },
    "easy_2": {
        "difficulty": "easy",
        "description": "Extract the single action item from a brief project check-in.",
        "transcript": (
            "Project check-in — Tuesday 2 PM\n"
            "Manager: We need the Q2 budget report. Sarah, please send it to "
            "finance by Friday.\n"
            "Sarah: Will do.\n"
            "Manager: Thanks, that's all."
        ),
        "ground_truth": [
            {"who": "Sarah", "what": "send Q2 budget report to finance", "deadline": "Friday"}
        ],
    },
    "easy_3": {
        "difficulty": "easy",
        "description": "Extract the action item from a quick sales sync.",
        "transcript": (
            "Sales sync — Monday 10 AM\n"
            "VP Sales: The Acme Corp demo is Thursday. Kevin, set up the demo "
            "environment and load sample data by Wednesday morning.\n"
            "Kevin: Got it.\n"
            "VP Sales: Perfect, let's move on."
        ),
        "ground_truth": [
            {"who": "Kevin", "what": "set up demo environment and load sample data", "deadline": "Wednesday morning"}
        ],
    },
    "easy_4": {
        "difficulty": "easy",
        "description": "Extract the action item from an HR check-in.",
        "transcript": (
            "HR check-in — Tuesday 3 PM\n"
            "HR Manager: Annual reviews are coming up. Diana, please collect all "
            "self-assessment forms from your team and submit them by next Monday.\n"
            "Diana: Sure, I'll send reminders today.\n"
            "HR Manager: Great, thanks."
        ),
        "ground_truth": [
            {"who": "Diana", "what": "collect self-assessment forms from team and submit them", "deadline": "next Monday"}
        ],
    },
    "easy_5": {
        "difficulty": "easy",
        "description": "Extract the action item from a design review.",
        "transcript": (
            "Design review — Wednesday 11 AM\n"
            "Lead Designer: The new dashboard looks good overall but the color "
            "contrast on the sidebar fails accessibility checks. Marcus, update the "
            "sidebar colors to meet WCAG AA standards by end of day today.\n"
            "Marcus: On it.\n"
            "Lead Designer: Thanks, send me a screenshot when done."
        ),
        "ground_truth": [
            {"who": "Marcus", "what": "update sidebar colors to meet WCAG AA standards", "deadline": "end of day today"}
        ],
    },
    "easy_6": {
        "difficulty": "easy",
        "description": "Extract the action item from a security standup.",
        "transcript": (
            "Security standup — Thursday 9 AM\n"
            "CISO: We found a critical CVE in our logging library. Yuki, patch all "
            "production instances and verify the fix by Friday 5 PM.\n"
            "Yuki: Understood, I'll start immediately.\n"
            "CISO: Good. Report back once verified."
        ),
        "ground_truth": [
            {"who": "Yuki", "what": "patch production instances and verify the logging library fix", "deadline": "Friday 5 PM"}
        ],
    },
    "easy_7": {
        "difficulty": "easy",
        "description": "Extract the action item from a marketing sync.",
        "transcript": (
            "Marketing sync — Monday 2 PM\n"
            "Marketing Director: We're launching the new feature next Tuesday. "
            "Olivia, write the press release draft and have it ready for review by "
            "Thursday afternoon.\n"
            "Olivia: Will do, I'll base it on the product brief.\n"
            "Marketing Director: Perfect."
        ),
        "ground_truth": [
            {"who": "Olivia", "what": "write the press release draft", "deadline": "Thursday afternoon"}
        ],
    },
    "easy_8": {
        "difficulty": "easy",
        "description": "Extract the action item from an ops incident debrief.",
        "transcript": (
            "Ops debrief — Wednesday 4 PM\n"
            "SRE Lead: The staging environment crashed again because of memory leaks. "
            "Tyler, add memory limit alerts to our monitoring dashboard by tomorrow morning.\n"
            "Tyler: Sure, I'll set them up in Grafana.\n"
            "SRE Lead: Thanks, let's catch these earlier next time."
        ),
        "ground_truth": [
            {"who": "Tyler", "what": "add memory limit alerts to monitoring dashboard", "deadline": "tomorrow morning"}
        ],
    },
    "easy_9": {
        "difficulty": "easy",
        "description": "Extract the action item from a finance check-in.",
        "transcript": (
            "Finance check-in — Friday 10 AM\n"
            "CFO: The March expense reconciliation is overdue. Priya, please finish "
            "reconciling all department expenses and send the summary to accounting "
            "by next Tuesday.\n"
            "Priya: I'll have it done.\n"
            "CFO: Thank you."
        ),
        "ground_truth": [
            {"who": "Priya", "what": "finish reconciling department expenses and send summary to accounting", "deadline": "next Tuesday"}
        ],
    },
    "easy_10": {
        "difficulty": "easy",
        "description": "Extract the action item from an engineering 1:1.",
        "transcript": (
            "Engineering 1:1 — Thursday 2 PM\n"
            "Tech Lead: The API documentation hasn't been updated since the v2 launch. "
            "James, please update the REST API docs on Confluence by end of this week.\n"
            "James: I'll work on it after standup tomorrow.\n"
            "Tech Lead: Sounds good."
        ),
        "ground_truth": [
            {"who": "James", "what": "update REST API docs on Confluence", "deadline": "end of this week"}
        ],
    },

    # =====================================================================
    # MEDIUM — 3-4 action items, multiple speakers, clear but scattered
    # =====================================================================

    "medium_1": {
        "difficulty": "medium",
        "description": "Extract all action items from a multi-person planning meeting.",
        "transcript": (
            "Sprint planning — Wednesday 10 AM\n"
            "Alice: We need to finalize the API design. Tom, can you draft the "
            "OpenAPI spec by Thursday?\n"
            "Tom: Yes. I'll also need the data models from Priya.\n"
            "Alice: Priya, send the data model doc to Tom by end of day today.\n"
            "Priya: Got it.\n"
            "Alice: Also, Carlos, please update the project timeline on Jira "
            "before Friday standup.\n"
            "Carlos: Sure thing."
        ),
        "ground_truth": [
            {"who": "Tom", "what": "draft the OpenAPI spec", "deadline": "Thursday"},
            {"who": "Priya", "what": "send data model doc to Tom", "deadline": "today"},
            {"who": "Carlos", "what": "update project timeline on Jira", "deadline": "Friday"},
        ],
    },
    "medium_2": {
        "difficulty": "medium",
        "description": "Extract action items from a cross-team sync meeting.",
        "transcript": (
            "Cross-team sync — Thursday 3 PM\n"
            "Dev lead: The staging environment keeps crashing. Jun, investigate "
            "the memory leak and file a report by Monday.\n"
            "Jun: On it.\n"
            "Dev lead: QA team — Lisa, write regression tests for the payments "
            "module. Target next Wednesday.\n"
            "Lisa: Will do.\n"
            "Dev lead: And marketing — Dave, prepare the launch announcement "
            "draft by next Tuesday.\n"
            "Dave: Understood."
        ),
        "ground_truth": [
            {"who": "Jun", "what": "investigate memory leak and file report", "deadline": "Monday"},
            {"who": "Lisa", "what": "write regression tests for payments module", "deadline": "Wednesday"},
            {"who": "Dave", "what": "prepare launch announcement draft", "deadline": "Tuesday"},
        ],
    },
    "medium_3": {
        "difficulty": "medium",
        "description": "Extract action items from a product planning meeting.",
        "transcript": (
            "Product planning — Tuesday 11 AM\n"
            "PM: Let's plan the v3.2 release. We have three major items.\n"
            "PM: First, the search feature. Elena, finish the search indexing "
            "backend and have it deployed to staging by next Monday.\n"
            "Elena: Sure. The Elasticsearch cluster is ready, just need to wire it up.\n"
            "PM: Second, notifications. Raj, implement the push notification service "
            "and integrate with the mobile app. Deadline is next Wednesday.\n"
            "Raj: I'll coordinate with the iOS and Android teams.\n"
            "PM: And third, analytics. Mei, build the new analytics dashboard using "
            "the designs from last sprint. Have it demo-ready by next Friday.\n"
            "Mei: Got it. I'll pull the Figma files today.\n"
            "PM: Great. Let's check in Thursday."
        ),
        "ground_truth": [
            {"who": "Elena", "what": "finish search indexing backend and deploy to staging", "deadline": "next Monday"},
            {"who": "Raj", "what": "implement push notification service and integrate with mobile app", "deadline": "next Wednesday"},
            {"who": "Mei", "what": "build new analytics dashboard from designs", "deadline": "next Friday"},
        ],
    },
    "medium_4": {
        "difficulty": "medium",
        "description": "Extract action items from a client onboarding meeting.",
        "transcript": (
            "Client onboarding — Globex Corp — Monday 1 PM\n"
            "Account Manager: Welcome everyone. Let's go through onboarding steps.\n"
            "Account Manager: First, Liam, create the Globex workspace in our "
            "platform and configure SSO by Wednesday.\n"
            "Liam: I'll need their IdP metadata. Can someone request that?\n"
            "Account Manager: Good point. Zoe, email the Globex IT contact and "
            "request the SAML metadata by tomorrow.\n"
            "Zoe: On it.\n"
            "Account Manager: Next, Aisha, prepare the customized training materials "
            "using the Globex brand guidelines. Have them ready by Thursday.\n"
            "Aisha: Sure, I'll use the template from last quarter.\n"
            "Account Manager: Finally, Omar, set up the data migration pipeline and "
            "run a test import of their sample dataset by Friday.\n"
            "Omar: I'll start once Liam has the workspace ready.\n"
            "Account Manager: Great, keep me posted."
        ),
        "ground_truth": [
            {"who": "Liam", "what": "create Globex workspace and configure SSO", "deadline": "Wednesday"},
            {"who": "Zoe", "what": "email Globex IT contact and request SAML metadata", "deadline": "tomorrow"},
            {"who": "Aisha", "what": "prepare customized training materials with Globex brand guidelines", "deadline": "Thursday"},
            {"who": "Omar", "what": "set up data migration pipeline and run test import", "deadline": "Friday"},
        ],
    },
    "medium_5": {
        "difficulty": "medium",
        "description": "Extract action items from a release planning meeting.",
        "transcript": (
            "Release planning — v4.0 — Wednesday 3 PM\n"
            "Release Manager: v4.0 ships in two weeks. Here's what's outstanding.\n"
            "Release Manager: Chen, the database migration scripts need to be "
            "finalized and tested against the production schema. Due by Monday.\n"
            "Chen: I've got the draft scripts, just need to handle the edge cases.\n"
            "Release Manager: Fatima, update the CHANGELOG and release notes. "
            "Include all breaking changes. Due by next Tuesday.\n"
            "Fatima: I'll coordinate with Chen on the migration section.\n"
            "Release Manager: And Sophie, run the full regression suite on staging "
            "and send the test report to the team by next Wednesday.\n"
            "Sophie: Will do. I'll flag any blockers immediately.\n"
            "Release Manager: Perfect. Let's stay on track."
        ),
        "ground_truth": [
            {"who": "Chen", "what": "finalize and test database migration scripts against production schema", "deadline": "Monday"},
            {"who": "Fatima", "what": "update CHANGELOG and release notes with breaking changes", "deadline": "next Tuesday"},
            {"who": "Sophie", "what": "run full regression suite on staging and send test report", "deadline": "next Wednesday"},
        ],
    },
    "medium_6": {
        "difficulty": "medium",
        "description": "Extract action items from a team retrospective.",
        "transcript": (
            "Sprint retrospective — Friday 4 PM\n"
            "Scrum Master: What went well, what needs improvement?\n"
            "Dev A: Deployments took too long this sprint. We should automate the "
            "smoke tests.\n"
            "Scrum Master: Good idea. Natasha, create a CI job for automated smoke "
            "tests and have a prototype by next Wednesday.\n"
            "Natasha: I can do that.\n"
            "Dev B: The code review queue was backed up. We waited 2 days on some PRs.\n"
            "Scrum Master: Agreed. Victor, draft a code review SLA document — max "
            "24-hour turnaround — and share it with the team by Monday.\n"
            "Victor: Makes sense, I'll propose some guidelines.\n"
            "Dev C: Our monitoring missed the latency spike on Tuesday.\n"
            "Scrum Master: Wendy, add P95 latency alerts for all critical endpoints "
            "to PagerDuty. Let's have that done by next Thursday.\n"
            "Wendy: I'll coordinate with the SRE team.\n"
            "Scrum Master: Good retro. Let's execute on these."
        ),
        "ground_truth": [
            {"who": "Natasha", "what": "create CI job for automated smoke tests", "deadline": "next Wednesday"},
            {"who": "Victor", "what": "draft code review SLA document with 24-hour turnaround", "deadline": "Monday"},
            {"who": "Wendy", "what": "add P95 latency alerts for critical endpoints to PagerDuty", "deadline": "next Thursday"},
        ],
    },
    "medium_7": {
        "difficulty": "medium",
        "description": "Extract action items from a budget review meeting.",
        "transcript": (
            "Budget review — Q3 planning — Thursday 10 AM\n"
            "CFO: Let's finalize Q3 allocations.\n"
            "CFO: Engineering — Hannah, prepare a cost breakdown of our cloud "
            "infrastructure. Include reserved instance options. Due next Monday.\n"
            "Hannah: I'll pull the AWS billing reports.\n"
            "CFO: Marketing — Derek, submit the Q3 campaign budget with ROI "
            "projections from last quarter. Due next Tuesday.\n"
            "Derek: I'll have the spreadsheet ready.\n"
            "CFO: Operations — Kira, compile vendor contract renewal costs and "
            "identify any contracts up for renegotiation. Due next Wednesday.\n"
            "Kira: Several contracts are up in July, I'll flag them.\n"
            "CFO: And HR — Lucas, estimate hiring costs for the 5 approved positions "
            "including recruiter fees and onboarding. Due next Thursday.\n"
            "Lucas: I'll factor in the new salary bands.\n"
            "CFO: I need all of these before the board meeting on the 15th."
        ),
        "ground_truth": [
            {"who": "Hannah", "what": "prepare cloud infrastructure cost breakdown with reserved instance options", "deadline": "next Monday"},
            {"who": "Derek", "what": "submit Q3 campaign budget with ROI projections", "deadline": "next Tuesday"},
            {"who": "Kira", "what": "compile vendor contract renewal costs and identify renegotiation opportunities", "deadline": "next Wednesday"},
            {"who": "Lucas", "what": "estimate hiring costs for approved positions including recruiter fees", "deadline": "next Thursday"},
        ],
    },
    "medium_8": {
        "difficulty": "medium",
        "description": "Extract action items from an infrastructure planning meeting.",
        "transcript": (
            "Infrastructure planning — Monday 2 PM\n"
            "CTO: We're migrating to Kubernetes next quarter. Three prep tasks.\n"
            "CTO: Andre, containerize the authentication service and write Helm "
            "charts for it. Target next Friday.\n"
            "Andre: The Dockerfile is mostly done, just need the Helm piece.\n"
            "CTO: Bianca, set up a staging Kubernetes cluster on GKE and configure "
            "the CI/CD pipeline to deploy there. Target two weeks from now.\n"
            "Bianca: I'll start with Terraform for the cluster setup.\n"
            "CTO: And Chris, document the migration runbook covering rollback "
            "procedures and health checks. Have a first draft by next Wednesday.\n"
            "Chris: I'll base it on our current runbook and add K8s specifics.\n"
            "CTO: This is a priority. Keep me updated daily."
        ),
        "ground_truth": [
            {"who": "Andre", "what": "containerize authentication service and write Helm charts", "deadline": "next Friday"},
            {"who": "Bianca", "what": "set up staging Kubernetes cluster on GKE and configure CI/CD pipeline", "deadline": "two weeks from now"},
            {"who": "Chris", "what": "document migration runbook with rollback procedures and health checks", "deadline": "next Wednesday"},
        ],
    },
    "medium_9": {
        "difficulty": "medium",
        "description": "Extract action items from a hiring committee meeting.",
        "transcript": (
            "Hiring committee — Wednesday 1 PM\n"
            "Head of Eng: We have three roles to fill urgently.\n"
            "Head of Eng: Grace, finalize the senior backend engineer job description "
            "and post it on LinkedIn and our careers page by Thursday.\n"
            "Grace: I'll update the requirements section first.\n"
            "Head of Eng: Hugo, schedule phone screens for the 8 shortlisted frontend "
            "candidates. Try to get them all done by next Tuesday.\n"
            "Hugo: I'll send calendar invites today.\n"
            "Head of Eng: And Isabella, prepare the take-home coding challenge for "
            "the DevOps role. Make sure it tests Terraform and Docker skills. "
            "Ready by Friday.\n"
            "Isabella: I'll base it on our actual infra setup.\n"
            "Head of Eng: Diversity is a priority — make sure our pipeline reflects that."
        ),
        "ground_truth": [
            {"who": "Grace", "what": "finalize senior backend engineer job description and post on LinkedIn and careers page", "deadline": "Thursday"},
            {"who": "Hugo", "what": "schedule phone screens for shortlisted frontend candidates", "deadline": "next Tuesday"},
            {"who": "Isabella", "what": "prepare take-home coding challenge for DevOps role testing Terraform and Docker", "deadline": "Friday"},
        ],
    },
    "medium_10": {
        "difficulty": "medium",
        "description": "Extract action items from a training session planning meeting.",
        "transcript": (
            "Training planning — new engineer onboarding — Thursday 11 AM\n"
            "Engineering Manager: Three new engineers start on the 15th. Let's prep.\n"
            "Engineering Manager: Kelly, set up their development environments — "
            "laptops, Git access, VPN, IDE licenses. Everything ready by the 14th.\n"
            "Kelly: I'll coordinate with IT.\n"
            "Engineering Manager: Leo, prepare a 2-day onboarding curriculum covering "
            "our architecture, coding standards, and deployment process. Draft by "
            "next Monday.\n"
            "Leo: I'll update last quarter's slides.\n"
            "Engineering Manager: And Monica, assign each new hire a buddy from the "
            "team and set up intro coffee chats. Have the pairings done by next Wednesday.\n"
            "Monica: I'll ask for volunteers.\n"
            "Engineering Manager: First impressions matter — let's make onboarding great."
        ),
        "ground_truth": [
            {"who": "Kelly", "what": "set up development environments for new engineers including laptops Git access VPN and IDE licenses", "deadline": "the 14th"},
            {"who": "Leo", "what": "prepare 2-day onboarding curriculum covering architecture coding standards and deployment", "deadline": "next Monday"},
            {"who": "Monica", "what": "assign buddies to new hires and set up intro coffee chats", "deadline": "next Wednesday"},
        ],
    },

    # =====================================================================
    # HARD — long transcripts, implicit owners, vague deadlines,
    #         red herrings, superseded decisions, negated actions,
    #         cross-references, buried action items
    # =====================================================================

    "hard_1": {
        "difficulty": "hard",
        "description": "Extract action items from a messy quarterly review with vague commitments.",
        "transcript": (
            "Quarterly review — Friday 11 AM\n"
            "VP: Revenue is down 8%. I want the root cause analysis before the "
            "board meeting next Thursday.\n"
            "Finance lead: We can probably pull the numbers together... I'll try "
            "to loop in analytics.\n"
            "VP: Rachel, own the analysis. Coordinate with analytics and have a "
            "draft slide deck before Wednesday so I can review it.\n"
            "Rachel: Okay. Should I also update the forecast model?\n"
            "VP: Yes — update the forecast model too. Same deadline.\n"
            "VP: Oh and someone should book the boardroom. Mike, can you handle "
            "logistics?\n"
            "Mike: I'll take care of it by Monday."
        ),
        "ground_truth": [
            {"who": "Rachel", "what": "prepare root cause analysis slide deck", "deadline": "Wednesday"},
            {"who": "Rachel", "what": "update the forecast model", "deadline": "Wednesday"},
            {"who": "Mike", "what": "book the boardroom and handle logistics", "deadline": "Monday"},
        ],
    },
    "hard_2": {
        "difficulty": "hard",
        "description": "Extract action items from an informal meeting with implied owners.",
        "transcript": (
            "Ad-hoc sync — Monday afternoon\n"
            "Team lead: The client demo is sometime next week, probably Thursday "
            "or Friday. We need the frontend polished.\n"
            "Nora: I can handle the UI fixes. Might need design assets from "
            "Sam though.\n"
            "Team lead: Sam, get the updated mockups to Nora soon — let's say "
            "by tomorrow end of day.\n"
            "Sam: Okay.\n"
            "Team lead: Also, we realized nobody wrote the demo script. Nora, "
            "since you know the flow, can you draft it before Wednesday?\n"
            "Nora: Sure, I'll handle both.\n"
            "Team lead: And everyone — please test your features on staging before "
            "the demo. No specific deadline but do it before Thursday at latest."
        ),
        "ground_truth": [
            {"who": "Nora", "what": "fix frontend UI issues", "deadline": "before demo"},
            {"who": "Sam", "what": "send updated mockups to Nora", "deadline": "tomorrow"},
            {"who": "Nora", "what": "draft the demo script", "deadline": "Wednesday"},
            {"who": "everyone", "what": "test features on staging", "deadline": "Thursday"},
        ],
    },
    "hard_3": {
        "difficulty": "hard",
        "description": "Long all-hands with many speakers; action items buried in discussion.",
        "transcript": (
            "Company all-hands — Monday 10 AM — 45 attendees\n\n"
            "CEO: Good morning everyone. Big quarter ahead. Let me start with updates.\n"
            "CEO: Revenue grew 12% but churn increased. We need to address that.\n"
            "Head of Sales: Our pipeline is strong. We closed the Meridian deal last "
            "week — $2.3M ARR. The team did great work on that.\n"
            "CEO: Congrats to the sales team on Meridian.\n"
            "Head of Product: We shipped 14 features last quarter. Customer feedback "
            "on the new search is overwhelmingly positive. NPS went from 34 to 41.\n"
            "CEO: Great progress. Now let's talk about churn.\n"
            "Head of CS: Most churn is in the mid-market segment. Common complaints "
            "are onboarding complexity and missing integrations.\n"
            "CEO: We need a plan. Vanessa, put together a churn reduction proposal "
            "with specific initiatives and present it at the leadership offsite on "
            "the 20th.\n"
            "Vanessa: I'll work with CS and Product on that.\n"
            "Head of Eng: On the technical side, we had three P1 incidents last month. "
            "Two were database related.\n"
            "CEO: That's too many. What's the fix?\n"
            "Head of Eng: We need to migrate the user table to the new sharded setup. "
            "It's been on the roadmap for months.\n"
            "CEO: Prioritize it. Who's leading the migration?\n"
            "Head of Eng: Kirk is the best person for it.\n"
            "CEO: Kirk, own the database migration. I want a timeline and risk "
            "assessment by next Friday.\n"
            "Kirk: I'll scope it out this week.\n"
            "Head of HR: Quick update — we're launching the new benefits package. "
            "Everyone should review it on the intranet.\n"
            "CEO: Thanks. On a separate note, our website is outdated. It still "
            "shows last year's product screenshots.\n"
            "Head of Marketing: We know. It's been deprioritized.\n"
            "CEO: Let's not deprioritize it anymore. Tanya, refresh the website "
            "with current product screenshots and updated customer logos. Deadline "
            "is end of month.\n"
            "Tanya: I'll coordinate with design.\n"
            "CEO: One more thing — the annual company retreat. We need a venue.\n"
            "Head of Ops: I've been looking at options.\n"
            "CEO: Good. Just make sure we have a confirmed venue and agenda by "
            "April 1st. You own it, right?\n"
            "Head of Ops: Yes, I'll finalize it.\n"
            "CEO: Alright, great all-hands. Let's execute."
        ),
        "ground_truth": [
            {"who": "Vanessa", "what": "prepare churn reduction proposal with specific initiatives", "deadline": "the 20th"},
            {"who": "Kirk", "what": "scope database migration and provide timeline and risk assessment", "deadline": "next Friday"},
            {"who": "Tanya", "what": "refresh website with current product screenshots and updated customer logos", "deadline": "end of month"},
            {"who": "Head of Ops", "what": "finalize retreat venue and agenda", "deadline": "April 1st"},
        ],
    },
    "hard_4": {
        "difficulty": "hard",
        "description": "Two meetings merged — morning standup and afternoon planning. Separate the action items.",
        "transcript": (
            "=== Morning standup — 9:30 AM ===\n"
            "Scrum Master: Quick updates. Who's blocked?\n"
            "Dev A (Ravi): I'm blocked on the API gateway. Need DevOps to open port "
            "443 on staging.\n"
            "Scrum Master: Carla, can you unblock Ravi? Open port 443 on staging "
            "today.\n"
            "Carla: I'll do it after this meeting.\n"
            "Dev B (Suki): The unit tests are flaky again. Random timeouts.\n"
            "Scrum Master: Known issue. We'll address it in planning.\n"
            "Dev C (Youssef): I finished the payment refund feature. Needs code review.\n"
            "Scrum Master: Ravi, review Youssef's PR when you're unblocked. Try by "
            "end of day.\n"
            "Ravi: Sure.\n\n"
            "=== Afternoon sprint planning — 2:00 PM ===\n"
            "PM: Alright, sprint 14 priorities.\n"
            "PM: First priority is fixing the flaky tests. Suki, you brought it up "
            "this morning. Take ownership — isolate the timeout root cause and fix "
            "it. We need stable CI by end of sprint, so next Friday.\n"
            "Suki: I have a theory it's the database connection pool. I'll investigate.\n"
            "PM: Second, the multi-currency feature. Youssef, since you just finished "
            "refunds, pick up the multi-currency backend. Spec is in Confluence. "
            "Target next Wednesday for the API endpoints.\n"
            "Youssef: Got it.\n"
            "PM: Third, the admin dashboard needs export functionality. Ravi, after "
            "the code review, start on CSV and PDF export for the admin reports. "
            "Demo-ready by next Thursday.\n"
            "Ravi: That's tight but doable.\n"
            "PM: Good sprint. Let's go."
        ),
        "ground_truth": [
            {"who": "Carla", "what": "open port 443 on staging to unblock Ravi", "deadline": "today"},
            {"who": "Ravi", "what": "review Youssef's payment refund PR", "deadline": "end of day"},
            {"who": "Suki", "what": "isolate and fix flaky test timeout root cause for stable CI", "deadline": "next Friday"},
            {"who": "Youssef", "what": "implement multi-currency backend API endpoints", "deadline": "next Wednesday"},
            {"who": "Ravi", "what": "build CSV and PDF export for admin reports", "deadline": "next Thursday"},
        ],
    },
    "hard_5": {
        "difficulty": "hard",
        "description": "Meeting with superseded and changed decisions. Only the final decisions count.",
        "transcript": (
            "Feature planning — Thursday 2 PM\n"
            "PM: Let's figure out the notification system.\n"
            "PM: Wei, can you build the email notification service? Target next Monday.\n"
            "Wei: Sure. Should I use SendGrid or our internal SMTP?\n"
            "PM: Use SendGrid for now.\n"
            "Tech Lead: Actually, wait. Legal flagged that SendGrid's data residency "
            "doesn't meet our EU requirements. We need to use Postmark instead.\n"
            "PM: Good catch. Wei, scratch SendGrid — use Postmark. Same deadline.\n"
            "Wei: Okay, Postmark it is.\n"
            "PM: Next, the push notifications. Daria, handle mobile push via Firebase.\n"
            "Daria: Firebase doesn't support our custom payload format.\n"
            "PM: Then what do you suggest?\n"
            "Daria: I can use AWS SNS. It supports custom payloads.\n"
            "PM: Fine. Daria, implement push notifications using AWS SNS. Due "
            "next Wednesday.\n"
            "Tech Lead: Also, we need rate limiting on the notification service to "
            "prevent spam. Felix, add rate limiting middleware. Thursday deadline.\n"
            "Felix: What rate limits?\n"
            "Tech Lead: Start with 100 per user per hour. We can adjust later.\n"
            "PM: Actually Felix, hold off on rate limiting. Let's ship the core "
            "notifications first and add rate limiting in the next sprint.\n"
            "Tech Lead: Fair enough.\n"
            "PM: So to recap: Wei on email with Postmark by Monday, Daria on push "
            "with SNS by Wednesday. Felix, you're free to help with testing instead. "
            "Felix, write integration tests for both services by next Friday.\n"
            "Felix: On it."
        ),
        "ground_truth": [
            {"who": "Wei", "what": "build email notification service using Postmark", "deadline": "next Monday"},
            {"who": "Daria", "what": "implement push notifications using AWS SNS", "deadline": "next Wednesday"},
            {"who": "Felix", "what": "write integration tests for notification services", "deadline": "next Friday"},
        ],
    },
    "hard_6": {
        "difficulty": "hard",
        "description": "Meeting with extremely vague and relative deadlines requiring inference.",
        "transcript": (
            "Informal planning — coffee chat — Tuesday afternoon\n"
            "Director: The investor update is coming up. Not sure when exactly — "
            "probably sometime in the third week of the month.\n"
            "Analyst (Rita): I can start pulling the financial data.\n"
            "Director: Yeah, Rita, get the revenue and burn rate numbers together. "
            "Sooner the better, but definitely before the update.\n"
            "Director: Oh and the product metrics. We need MAU, DAU, retention. "
            "Gautam, can you pull those from Amplitude?\n"
            "Gautam: When do you need them?\n"
            "Director: A few days before the investor update. So... maybe end of "
            "next week? Give or take?\n"
            "Gautam: I'll aim for that.\n"
            "Director: The slide deck from last quarter is mostly reusable. Priti, "
            "update the deck with new numbers once Rita and Gautam have their data. "
            "You'll probably have a couple of days to do it.\n"
            "Priti: So maybe the week after Gautam's done?\n"
            "Director: Something like that. Just don't leave it to the last minute.\n"
            "Director: Also, someone should update the cap table. It's been wrong "
            "since the last round.\n"
            "Rita: I can do that too.\n"
            "Director: Great. No huge rush on the cap table — but before the update "
            "for sure."
        ),
        "ground_truth": [
            {"who": "Rita", "what": "compile revenue and burn rate financial data", "deadline": "before investor update"},
            {"who": "Gautam", "what": "pull MAU DAU and retention metrics from Amplitude", "deadline": "end of next week"},
            {"who": "Priti", "what": "update investor slide deck with new numbers", "deadline": "after data is ready before investor update"},
            {"who": "Rita", "what": "update the cap table", "deadline": "before investor update"},
        ],
    },
    "hard_7": {
        "difficulty": "hard",
        "description": "Long brainstorming session with lots of ideas but few real commitments.",
        "transcript": (
            "Product brainstorm — innovation hour — Friday 3 PM\n"
            "PM: Let's throw ideas around for Q4. No bad ideas.\n"
            "Dev A: What about AI-powered search? We could use embeddings.\n"
            "Dev B: That's cool but expensive. Maybe a simpler autocomplete first?\n"
            "PM: I like both ideas. Let's keep them on the board.\n"
            "Designer: What about a complete redesign of the dashboard? Users hate "
            "the current layout.\n"
            "PM: That's ambitious. Let's not commit to a full redesign yet.\n"
            "Dev C: We should consider a mobile app. Our competitors all have one.\n"
            "PM: True. That's a big investment though.\n"
            "Dev A: What if we start with a PWA? Lower investment.\n"
            "PM: Interesting. Let me think about it.\n"
            "Dev B: Can we at least fix the performance issues? The dashboard loads "
            "in 8 seconds.\n"
            "PM: That's not a brainstorm item — that's a bug. Yes, let's fix it.\n"
            "PM: Dev B — actually, Hana, profile the dashboard performance and "
            "identify the top 3 bottlenecks. Have the analysis ready by next Tuesday.\n"
            "Hana (Dev B): Sure.\n"
            "PM: I'm going to write up the brainstorm ideas as a product brief. "
            "Let's revisit in two weeks.\n"
            "Designer: Should I explore the dashboard redesign in the meantime?\n"
            "PM: No, don't start on it. We haven't committed to it.\n"
            "PM: Actually, one concrete thing — Dev A, Naveen, could you do a quick "
            "spike on embedding-based search? Just a proof of concept, nothing "
            "production. Spend no more than 2 days on it. Report back next Thursday.\n"
            "Naveen (Dev A): I'll use the OpenAI embeddings API.\n"
            "PM: And I'll write the brainstorm summary. Give me until Monday.\n"
            "PM: That's it. Good session."
        ),
        "ground_truth": [
            {"who": "Hana", "what": "profile dashboard performance and identify top 3 bottlenecks", "deadline": "next Tuesday"},
            {"who": "Naveen", "what": "build proof of concept for embedding-based search", "deadline": "next Thursday"},
            {"who": "PM", "what": "write brainstorm summary as product brief", "deadline": "Monday"},
        ],
    },
    "hard_8": {
        "difficulty": "hard",
        "description": "Crisis incident response with rapid-fire assignments under pressure.",
        "transcript": (
            "P0 Incident — Production outage — Saturday 2:17 AM (emergency bridge)\n\n"
            "Incident Commander (Alina): Alright, production is down. Payments are "
            "failing. Customer-facing. All hands.\n"
            "Alina: Status — what do we know?\n"
            "On-call SRE (Ben): The payment gateway is returning 503s. Started 12 "
            "minutes ago. I've checked the load balancer — it's healthy.\n"
            "Alina: Could be the gateway provider. Ben, contact Stripe support "
            "immediately and open a priority ticket. I need an update in 15 minutes.\n"
            "Ben: On it.\n"
            "Alina: Meanwhile, it could be on our side. Dina, check the payment "
            "service logs and database connections. Look for connection pool exhaustion "
            "or OOM kills.\n"
            "Dina: Checking now.\n"
            "Alina: Customer impact — we need to communicate. Eric, draft a status "
            "page update acknowledging the issue. Post it within 10 minutes.\n"
            "Eric: Writing it now.\n"
            "Alina: I also want a rollback option ready. Faisal, prepare a rollback "
            "of the last deployment — we pushed a payment service update at 11 PM. "
            "Don't execute yet, just have it ready.\n"
            "Faisal: Pulling up the rollback runbook.\n"
            "[5 minutes later]\n"
            "Dina: Found it — the connection pool is maxed out. The 11 PM deploy "
            "introduced a connection leak in the retry logic.\n"
            "Alina: That's our root cause. Faisal, execute the rollback now.\n"
            "Faisal: Rolling back.\n"
            "Alina: Ben, cancel the Stripe ticket — it's on our side.\n"
            "Ben: Got it.\n"
            "Alina: Eric, update the status page — root cause identified, fix in "
            "progress.\n"
            "Eric: Updated.\n"
            "Alina: Once we're stable, Dina, write the postmortem. I want it by "
            "Monday end of day. Include the timeline, root cause, and remediation steps.\n"
            "Dina: Will do.\n"
            "Alina: And Faisal, add a connection pool monitoring alert so we catch "
            "this next time. Have it in place by Tuesday.\n"
            "Faisal: I'll add it to Datadog.\n"
            "Alina: Okay team, good response. Let's monitor for the next hour."
        ),
        "ground_truth": [
            {"who": "Eric", "what": "draft and post status page update acknowledging the outage", "deadline": "within 10 minutes"},
            {"who": "Faisal", "what": "execute rollback of the last payment service deployment", "deadline": "immediately"},
            {"who": "Dina", "what": "write postmortem with timeline root cause and remediation steps", "deadline": "Monday end of day"},
            {"who": "Faisal", "what": "add connection pool monitoring alert to Datadog", "deadline": "Tuesday"},
        ],
    },
    "hard_9": {
        "difficulty": "hard",
        "description": "Meeting with conditional actions, negated tasks, and red herrings.",
        "transcript": (
            "Strategy meeting — Wednesday 1 PM\n"
            "VP Eng: Let's discuss the platform consolidation.\n"
            "VP Eng: We were going to merge the two databases, but after the "
            "architecture review, that's off the table. Don't spend any more time "
            "on database merging.\n"
            "Lead A: What about the API consolidation?\n"
            "VP Eng: That's still on. Quinn, continue the API consolidation work. "
            "Merge the v1 and v2 endpoints into a unified v3 API. I need a design "
            "doc by next Monday.\n"
            "Quinn: Got it.\n"
            "VP Eng: If the security audit passes next week, we'll proceed with the "
            "public API launch. Rosa, prepare the API documentation and developer "
            "portal. But only if the audit passes — don't do anything until we "
            "get the results.\n"
            "Rosa: Understood. I'll wait for confirmation.\n"
            "VP Eng: The legacy monolith decomposition — I know some of you are "
            "excited about it. But we're NOT doing it this quarter. It's deferred "
            "to Q2. Please don't start on it.\n"
            "Lead B: What about the monitoring improvements?\n"
            "VP Eng: Yes, that's happening. Sam, set up distributed tracing across "
            "all microservices using Jaeger. Deadline is end of the month.\n"
            "Sam: I'll need to add the OpenTelemetry SDK to each service.\n"
            "VP Eng: That's fine. And one more — Tina, regardless of the audit, "
            "we need to rotate all API keys and secrets. That's a security hygiene "
            "task. Do it by next Friday.\n"
            "Tina: I'll use Vault to automate the rotation.\n"
            "VP Eng: Good. To be clear: API consolidation, distributed tracing, "
            "and key rotation are GO. Database merge and monolith decomposition "
            "are NOT. Questions?\n"
            "All: No.\n"
            "VP Eng: Good meeting."
        ),
        "ground_truth": [
            {"who": "Quinn", "what": "merge v1 and v2 endpoints into unified v3 API and write design doc", "deadline": "next Monday"},
            {"who": "Sam", "what": "set up distributed tracing across all microservices using Jaeger", "deadline": "end of the month"},
            {"who": "Tina", "what": "rotate all API keys and secrets", "deadline": "next Friday"},
        ],
    },
    "hard_10": {
        "difficulty": "hard",
        "description": "Cross-functional meeting with delegation chains and implicit ownership.",
        "transcript": (
            "Cross-functional planning — SOC 2 compliance — Tuesday 10 AM\n\n"
            "Compliance Officer (Dana): We start the SOC 2 audit in 6 weeks. "
            "There's a lot to do.\n"
            "Dana: First, access controls. Engineering needs to implement role-based "
            "access for all internal tools.\n"
            "Head of Eng: My team can handle it. Who specifically though?\n"
            "Dana: Whoever you assign. I just need it done in 3 weeks.\n"
            "Head of Eng: Okay, I'll figure out who internally. Let me get back to you.\n"
            "Dana: Fine, but I need a name and plan by end of this week. You own "
            "getting that to me.\n"
            "Head of Eng: Understood.\n"
            "Dana: Second, we need an incident response policy documented. Legal "
            "started a draft but it needs technical input.\n"
            "Legal (Maya): I have the draft. It needs SRE to add the technical "
            "runbook sections.\n"
            "Dana: SRE lead — that's you, Omar. Work with Maya to complete the "
            "incident response policy. Two weeks.\n"
            "Omar: I'll set up a working session with Maya.\n"
            "Dana: Third, vendor security assessments. We have 12 vendors and none "
            "have been assessed this year.\n"
            "Dana: Procurement — Jason, you own the vendor relationships. Collect "
            "security questionnaire responses from all 12 vendors. Four weeks.\n"
            "Jason: That's tight for 12 vendors. Some are slow to respond.\n"
            "Dana: Start immediately. Escalate non-responders to me after one week.\n"
            "Dana: Fourth, employee security training. Everyone needs to complete "
            "it before the audit.\n"
            "HR (Nadia): I can set that up.\n"
            "Dana: Nadia, roll out the security awareness training to all employees "
            "and track completion. I need 100% completion in 4 weeks.\n"
            "Nadia: I'll use our LMS.\n"
            "Dana: Let's meet weekly to track progress. Same time slot."
        ),
        "ground_truth": [
            {"who": "Head of Eng", "what": "assign someone for role-based access implementation and provide name and plan to Dana", "deadline": "end of this week"},
            {"who": "Omar", "what": "work with Maya to complete the incident response policy with technical runbook sections", "deadline": "two weeks"},
            {"who": "Jason", "what": "collect security questionnaire responses from all 12 vendors", "deadline": "four weeks"},
            {"who": "Nadia", "what": "roll out security awareness training to all employees and track completion", "deadline": "four weeks"},
        ],
    },
    "hard_11": {
        "difficulty": "hard",
        "description": "All-day offsite summary with scattered action items across sessions.",
        "transcript": (
            "Engineering offsite — summary notes — all day Friday\n\n"
            "=== Session 1: Technical Debt (9 AM) ===\n"
            "Facilitator: We identified the top technical debt items.\n"
            "Discussion ranged from the legacy auth system to the test suite. "
            "Team agreed the auth system is the biggest pain point but too large "
            "for one sprint. The test suite, however, is fixable.\n"
            "Conclusion: We will NOT tackle auth refactoring this quarter.\n"
            "Action: Priya will create a test reliability task force and produce "
            "a 2-week improvement plan. Due by next Wednesday.\n\n"
            "=== Session 2: Developer Experience (11 AM) ===\n"
            "Discussion about slow build times and complex local setup.\n"
            "Several ideas were proposed: remote dev environments, build caching, "
            "Docker Compose simplification. No agreement on remote dev envs — too "
            "expensive. Build caching got unanimous support.\n"
            "Action: Jorge will implement build caching with Turborepo and measure "
            "the improvement. Two weeks to show results.\n"
            "Note: Someone mentioned we should also standardize IDE configs. Nice "
            "idea but no one volunteered, so it's NOT an action item.\n\n"
            "=== Session 3: Team Processes (2 PM) ===\n"
            "Retrospective on sprint processes. Code review bottleneck discussed "
            "again. PR size is the main issue — too many large PRs.\n"
            "Action: Team agreed on a soft 400-line PR limit. Kara will update the "
            "CONTRIBUTING.md and add a CI check that warns on large PRs. Due next Monday.\n"
            "Discussion about on-call rotation. Current rotation is unfair — same "
            "people keep getting paged. Need a better schedule.\n"
            "Action: Lars will redesign the on-call rotation using PagerDuty's "
            "round-robin feature. New rotation starts in 3 weeks.\n\n"
            "=== Session 4: Wrap-up (4 PM) ===\n"
            "Quick wins mentioned: update the README (nobody assigned — skipped), "
            "archive old Slack channels (nice to have — skipped).\n"
            "Final action: Facilitator (Deepa) will compile all offsite action items "
            "into a tracking document and share with the team by end of day Monday."
        ),
        "ground_truth": [
            {"who": "Priya", "what": "create test reliability task force and produce 2-week improvement plan", "deadline": "next Wednesday"},
            {"who": "Jorge", "what": "implement build caching with Turborepo and measure improvement", "deadline": "two weeks"},
            {"who": "Kara", "what": "update CONTRIBUTING.md and add CI check warning on large PRs", "deadline": "next Monday"},
            {"who": "Lars", "what": "redesign on-call rotation using PagerDuty round-robin", "deadline": "3 weeks"},
            {"who": "Deepa", "what": "compile offsite action items into tracking document and share with team", "deadline": "Monday"},
        ],
    },
    "hard_12": {
        "difficulty": "hard",
        "description": "Chaotic meeting with interruptions, tangents, and speakers talking over each other.",
        "transcript": (
            "Weekly sync — Wednesday 3 PM — running 20 minutes late\n\n"
            "PM (Arun): Sorry everyone, let's dive in. Where are we on the "
            "migration?\n"
            "Dev A (Beth): Still working on the data mapping. It's more complex "
            "than we thought—\n"
            "Dev B (Carlos): Wait, are we still using the old schema or the new one? "
            "I thought we decided—\n"
            "Beth: New schema. That was decided last week.\n"
            "Carlos: Right. Sorry.\n"
            "Arun: Beth, when will the data mapping be complete?\n"
            "Beth: Probably Monday. Maybe Tuesday if the edge cases are bad.\n"
            "Arun: Let's say Tuesday to be safe. Beth, have the data mapping done "
            "and documented by Tuesday.\n"
            "Beth: Okay.\n"
            "Arun: Carlos, you were supposed to set up the staging environment. "
            "Where's that?\n"
            "Carlos: Almost done. I hit an issue with the SSL certs.\n"
            "Arun: When can you have it ready?\n"
            "Carlos: Tomorrow if IT gives me the wildcard cert.\n"
            "Arun: Okay. Carlos, staging environment with SSL configured by "
            "Thursday. Reach out to IT today.\n"
            "Carlos: Got it.\n"
            "Dev C (Fatima): Quick question — should I continue with the API "
            "wrapper or switch to the frontend integration?\n"
            "Arun: What's the status on the API wrapper?\n"
            "Fatima: 80% done. Two more endpoints.\n"
            "Arun: Finish the API wrapper first. Fatima, complete the remaining "
            "two API endpoints by Friday. Then switch to frontend.\n"
            "Fatima: Sure.\n"
            "Arun: Oh wait — the client demo. When is that again?\n"
            "Beth: Next Thursday.\n"
            "Arun: Right. We need demo data. Does anyone have—\n"
            "Carlos: I can generate synthetic data.\n"
            "Arun: Actually, let the QA team handle that. Gita from QA — can you "
            "prepare realistic demo data covering all user personas? Have it loaded "
            "in staging by next Wednesday, day before the demo.\n"
            "Gita: I'll need the schema from Beth.\n"
            "Arun: Beth will have it by Tuesday. Gita, coordinate with her. "
            "Wednesday deadline for demo data.\n"
            "Gita: Okay.\n"
            "Arun: I think that's it. Oh — one more thing. The documentation. "
            "It's completely outdated.\n"
            "Beth: I know. There's like 40 pages of—\n"
            "Arun: Let's not boil the ocean. Beth, just update the migration "
            "section of the docs after your mapping is done. Add it to your "
            "Tuesday deliverable.\n"
            "Beth: So data mapping AND updated docs by Tuesday?\n"
            "Arun: Yes. Alright, let's go."
        ),
        "ground_truth": [
            {"who": "Beth", "what": "complete data mapping documentation and update migration docs", "deadline": "Tuesday"},
            {"who": "Carlos", "what": "finish staging environment setup with SSL configuration", "deadline": "Thursday"},
            {"who": "Fatima", "what": "complete remaining two API endpoints", "deadline": "Friday"},
            {"who": "Gita", "what": "prepare realistic demo data covering all user personas and load in staging", "deadline": "next Wednesday"},
        ],
    },
}
