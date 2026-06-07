"""
manual_engine.py — Rule-Based CISLF Report Generator
=====================================================
Generates complete CISLF Strategic Analysis Reports using a structured
20-question assessment questionnaire and a rule-based scoring + text engine.

No AI API is required. The framework is applied through:
  1. A weighted questionnaire (5 questions × 4 pillars = 20 questions)
  2. Score normalisation to 0-10 per pillar
  3. Template-based text generation matched to score bands
  4. Structured report assembly in the canonical CISLF format

CISLF Framework — Comprehensive Intelligent Strategic Leadership Framework (CISLF)
Developed by: Mohammad Quasif, DBA Candidate
Institution:  Kennedy University of Baptist, France
Thesis:       Quasif, M. (2025). Strategic Leadership for AI-Driven Business
              Transformation: A Cross-Industry Framework for Technology
              Executives. DBA Thesis. Kennedy University of Baptist, France.
"""

import copy
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Score Bands
# ---------------------------------------------------------------------------
# Each band: (min_inclusive, max_inclusive, label)
SCORE_BANDS: List[Tuple[float, float, str]] = [
    (0.0, 3.9,  "Critical Attention"),
    (4.0, 5.4,  "Needs Development"),
    (5.5, 6.9,  "Developing"),
    (7.0, 8.4,  "Strong"),
    (8.5, 10.0, "Exemplary"),
]

BandKey = Tuple[float, float]   # type alias for template dict keys


def get_band(score: float) -> BandKey:
    """Return the score band tuple for a given score (0-10)."""
    for lo, hi, _ in SCORE_BANDS:
        if lo <= score <= hi:
            return (lo, hi)
    return (7.0, 8.4)   # safe default


def get_maturity_label(score: float) -> str:
    """Return the maturity status label string for a given score."""
    for lo, hi, label in SCORE_BANDS:
        if lo <= score <= hi:
            return label
    return "Strong"


# ---------------------------------------------------------------------------
# Industry Lists & Contextual Rules
# ---------------------------------------------------------------------------

INDUSTRIES: List[str] = [
    "IT services and service desk operations",
    "Banking and financial services",
    "Healthcare and hospital administration",
    "Manufacturing and plant operations",
    "Retail and e-commerce",
    "Education and learning services",
    "Public services and citizen support",
    "Telecommunications",
    "Logistics and transport",
    "Agriculture and rural services",
    "Human resources and shared services",
    "Cybersecurity operations"
]

INDUSTRY_RULES: Dict[str, Dict[str, str]] = {
    "IT services and service desk operations": {
        "risk": "Tools are deployed without clear ownership, operating metrics or frontline confidence.",
        "emphasis": "Alignment, service-value metrics and human review."
    },
    "Banking and financial services": {
        "risk": "Efficiency gains may create customer harm, false positives or weak explainability.",
        "emphasis": "Traceability, controls, risk ownership and responsible AI."
    },
    "Healthcare and hospital administration": {
        "risk": "Automation may affect safety, privacy and professional accountability.",
        "emphasis": "Human oversight, risk classification and user training."
    },
    "Manufacturing and plant operations": {
        "risk": "Model outputs are separated from production decisions and maintenance routines.",
        "emphasis": "Process redesign, data readiness and safety governance."
    },
    "Retail and e-commerce": {
        "risk": "Customer trust is damaged when AI recommendations are inaccurate or opaque.",
        "emphasis": "Customer-value metrics, feedback loops and escalation."
    },
    "Education and learning services": {
        "risk": "Teacher judgement may be weakened if AI is treated as a replacement.",
        "emphasis": "Augmentation, staff readiness and ethical boundaries."
    },
    "Public services and citizen support": {
        "risk": "Fairness and accountability risks affect vulnerable users.",
        "emphasis": "Transparency, appeals and accessible service design."
    },
    "Telecommunications": {
        "risk": "Alert overload and unclear escalation prevent value.",
        "emphasis": "Operational workflow, ownership and reliability metrics."
    },
    "Logistics and transport": {
        "risk": "AI advice is not embedded into dispatch, asset and customer workflows.",
        "emphasis": "Cross-functional coordination and measurable delivery outcomes."
    },
    "Agriculture and rural services": {
        "risk": "Low digital confidence and fragmented data limit adoption.",
        "emphasis": "Local usability, data quality and trust building."
    },
    "Human resources and shared services": {
        "risk": "Bias in AI-driven evaluation, hiring, and performance metrics negatively impacts employee trust.",
        "emphasis": "Fairness, transparency, human-in-the-loop review, and bias auditing."
    },
    "Cybersecurity operations": {
        "risk": "Over-reliance on automated threat detection leads to alert fatigue and missed novel attack vectors.",
        "emphasis": "Human-AI collaboration, explainable threat intelligence, and continuous red-teaming."
    }
}

# ---------------------------------------------------------------------------
# Industry-Specific Scoring Configuration
# ---------------------------------------------------------------------------
# pillar_weights: relative importance of each pillar for this industry (normalised internally)
# critical_questions: if answered <= 2, the pillar is soft-capped at 7.0
# synergy_pairs: if both pillars score >= 7.5, each receives +0.3 bonus
# score_note: explains to the user why weights are configured this way

INDUSTRY_SCORING_CONFIG: Dict[str, Dict] = {
    "Banking and financial services": {
        "pillar_weights":      {1: 1.0, 2: 1.1, 3: 1.0, 4: 1.4},
        "critical_questions":  ["p4_q2", "p4_q3"],
        "synergy_pairs":       [(2, 4)],
        "score_note": "Banking weights Governance 1.4x — regulatory compliance and algorithmic explainability are non-negotiable in this sector.",
    },
    "Healthcare and hospital administration": {
        "pillar_weights":      {1: 1.0, 2: 1.0, 3: 1.2, 4: 1.3},
        "critical_questions":  ["p4_q1", "p4_q2", "p3_q3"],
        "synergy_pairs":       [(3, 4)],
        "score_note": "Healthcare weights Governance 1.3x and Capability 1.2x — clinical safety, ethics committee oversight, and trained clinicians are foundational.",
    },
    "Manufacturing and plant operations": {
        "pillar_weights":      {1: 1.0, 2: 1.2, 3: 1.1, 4: 1.2},
        "critical_questions":  ["p2_q1", "p4_q5"],
        "synergy_pairs":       [(2, 3)],
        "score_note": "Manufacturing weights Alignment and Governance 1.2x — AI must integrate into production processes with clear safety governance.",
    },
    "IT services and service desk operations": {
        "pillar_weights":      {1: 1.1, 2: 1.3, 3: 1.1, 4: 1.0},
        "critical_questions":  ["p2_q1", "p2_q3"],
        "synergy_pairs":       [(1, 2)],
        "score_note": "IT Services weights Strategic Alignment 1.3x — AI tools must be directly tied to service delivery KPIs (CSAT, MTTR, resolution rates).",
    },
    "Retail and e-commerce": {
        "pillar_weights":      {1: 1.0, 2: 1.3, 3: 1.1, 4: 1.1},
        "critical_questions":  ["p2_q1", "p2_q5"],
        "synergy_pairs":       [(2, 3)],
        "score_note": "Retail weights Strategic Alignment 1.3x — every AI investment must trace directly to revenue, conversion, or customer satisfaction metrics.",
    },
    "Education and learning services": {
        "pillar_weights":      {1: 1.1, 2: 1.0, 3: 1.3, 4: 1.1},
        "critical_questions":  ["p3_q1", "p4_q1"],
        "synergy_pairs":       [(1, 3)],
        "score_note": "Education weights Capability 1.3x — educator buy-in, AI literacy, and ethical boundaries protect learner outcomes and professional autonomy.",
    },
    "Public services and citizen support": {
        "pillar_weights":      {1: 1.1, 2: 1.0, 3: 1.0, 4: 1.4},
        "critical_questions":  ["p4_q1", "p4_q2", "p4_q4"],
        "synergy_pairs":       [(1, 4)],
        "score_note": "Public Sector weights Governance 1.4x — fairness, appeal rights, transparency, and legal accountability to citizens are non-negotiable.",
    },
    "Telecommunications": {
        "pillar_weights":      {1: 1.0, 2: 1.2, 3: 1.1, 4: 1.2},
        "critical_questions":  ["p2_q3", "p4_q3"],
        "synergy_pairs":       [(2, 4)],
        "score_note": "Telecoms weights Alignment 1.2x and Governance 1.2x — network AI must align to SLA/QoS KPIs and comply with telecoms regulatory requirements.",
    },
    "Logistics and transport": {
        "pillar_weights":      {1: 1.0, 2: 1.3, 3: 1.1, 4: 1.1},
        "critical_questions":  ["p2_q3", "p2_q1"],
        "synergy_pairs":       [(2, 3)],
        "score_note": "Logistics weights Strategic Alignment 1.3x — AI route and dispatch optimisation must be fully embedded into operational workflows.",
    },
    "Agriculture and rural services": {
        "pillar_weights":      {1: 1.2, 2: 1.0, 3: 1.3, 4: 1.0},
        "critical_questions":  ["p3_q1", "p1_q4"],
        "synergy_pairs":       [(1, 3)],
        "score_note": "Agriculture weights Capability 1.3x and Leadership 1.2x — digital readiness of farmers and local leadership adoption are the primary barriers.",
    },
    "Human resources and shared services": {
        "pillar_weights":      {1: 1.0, 2: 1.1, 3: 1.1, 4: 1.3},
        "critical_questions":  ["p4_q2", "p4_q1"],
        "synergy_pairs":       [(3, 4)],
        "score_note": "HR weights Governance 1.3x — algorithmic bias in hiring, performance, and pay decisions creates direct legal liability and destroys employee trust.",
    },
    "Cybersecurity operations": {
        "pillar_weights":      {1: 1.1, 2: 1.1, 3: 1.2, 4: 1.1},
        "critical_questions":  ["p3_q3", "p4_q2"],
        "synergy_pairs":       [(3, 4)],
        "score_note": "Cybersecurity weights Capability 1.2x — human-AI teaming, analyst expertise, and fail-safe override protocols are critical when AI controls threat response.",
    },
}

# ---------------------------------------------------------------------------
# Questionnaire Definition  (universal fallback — used when industry = "Not specified")
# ---------------------------------------------------------------------------
# Structure: PILLAR_QUESTIONS[pillar_num] = {"title", "icon", "questions": [...]}
# Each question: {"id", "text", "weight", "options": [(value, label), ...]}

PILLAR_QUESTIONS: Dict[int, dict] = {
    1: {
        "title": "Leadership Mindset & Vision",
        "icon": "🎯",
        "questions": [
            {
                "id": "p1_q1",
                "text": "Does your C-suite have a formally documented AI vision and strategy?",
                "weight": 1.5,
                "options": [
                    (1, "No formal AI vision exists"),
                    (2, "Informal discussions only, nothing documented"),
                    (3, "Vision draft in development, not yet adopted"),
                    (4, "Documented vision exists but not widely communicated"),
                    (5, "Clear, board-endorsed vision actively championed across the org"),
                ],
            },
            {
                "id": "p1_q2",
                "text": "How frequently does executive leadership formally review AI transformation progress?",
                "weight": 1.0,
                "options": [
                    (1, "Never or only reactively"),
                    (2, "Annually — included in yearly strategy review only"),
                    (3, "Quarterly — periodic structured reviews"),
                    (4, "Monthly — regular leadership AI progress meetings"),
                    (5, "Weekly / continuous — AI integrated into all leadership reviews"),
                ],
            },
            {
                "id": "p1_q3",
                "text": "Is there a dedicated AI/Digital leader (e.g., CAIO, CDO, AI VP) with real authority?",
                "weight": 1.2,
                "options": [
                    (1, "No dedicated role — AI is nobody's primary responsibility"),
                    (2, "AI is an informal responsibility split across existing roles"),
                    (3, "Part-time or shared role with limited authority"),
                    (4, "Dedicated role exists but with constrained mandate or budget"),
                    (5, "Empowered C-suite AI leader with board access, mandate and budget"),
                ],
            },
            {
                "id": "p1_q4",
                "text": "How would you rate executive-level AI literacy and strategic understanding?",
                "weight": 1.0,
                "options": [
                    (1, "Very low — AI is largely misunderstood or feared"),
                    (2, "Basic awareness of AI concepts, no deep understanding"),
                    (3, "Moderate — executives understand key AI opportunities and risks"),
                    (4, "Strong — executives actively learning and engaging with AI topics"),
                    (5, "Exemplary — executives drive AI strategic discussions and decisions"),
                ],
            },
            {
                "id": "p1_q5",
                "text": "Does leadership visibly sponsor, participate in, and champion AI initiatives?",
                "weight": 1.3,
                "options": [
                    (1, "No visible executive sponsorship of any AI initiative"),
                    (2, "Passive endorsement only — name on a slide"),
                    (3, "Occasional visible support for high-profile AI projects"),
                    (4, "Regular active sponsorship with personal involvement"),
                    (5, "Deep personal investment — leaders role-model AI adoption"),
                ],
            },
        ],
    },

    2: {
        "title": "Strategic Business-Technology Alignment",
        "icon": "🔗",
        "questions": [
            {
                "id": "p2_q1",
                "text": "Are AI initiatives directly tied to specific, measurable business outcomes (KPIs)?",
                "weight": 1.5,
                "options": [
                    (1, "No — AI projects are technology-led with no defined business KPIs"),
                    (2, "Loosely referenced to business goals but not measured"),
                    (3, "Some AI projects have defined business KPIs, others do not"),
                    (4, "Most AI initiatives have clear, tracked business metrics"),
                    (5, "All AI initiatives tightly linked to strategic KPIs with real-time tracking"),
                ],
            },
            {
                "id": "p2_q2",
                "text": "How mature is your AI portfolio management and investment prioritisation process?",
                "weight": 1.2,
                "options": [
                    (1, "No formal process — AI investments decided ad hoc"),
                    (2, "Informal prioritisation driven by IT or individuals"),
                    (3, "Basic portfolio tracking with some business input"),
                    (4, "Formal governance with business-led review and stage gates"),
                    (5, "Mature portfolio management with ROI tracking and dynamic rebalancing"),
                ],
            },
            {
                "id": "p2_q3",
                "text": "How effective is cross-functional collaboration between business and technology on AI?",
                "weight": 1.3,
                "options": [
                    (1, "Completely siloed — business and technology rarely interact"),
                    (2, "Limited collaboration, mostly at project boundaries"),
                    (3, "Some joint working exists but significant friction remains"),
                    (4, "Strong collaboration with shared goals and accountability"),
                    (5, "Fully integrated — co-ownership of AI outcomes across all functions"),
                ],
            },
            {
                "id": "p2_q4",
                "text": "How well does your technology roadmap align with and support the overall business strategy?",
                "weight": 1.0,
                "options": [
                    (1, "Technology roadmap is built independently of business strategy"),
                    (2, "Partial alignment — technology and business plans reviewed annually"),
                    (3, "Reasonable alignment with periodic joint reviews"),
                    (4, "Strong alignment — technology roadmap co-developed with business"),
                    (5, "Real-time strategic alignment — technology roadmap is a board-level tool"),
                ],
            },
            {
                "id": "p2_q5",
                "text": "Is there a formal business case and ROI framework applied to AI investments?",
                "weight": 1.0,
                "options": [
                    (1, "No — AI investments approved without structured business cases"),
                    (2, "Basic cost justification only, no ROI tracking"),
                    (3, "Business cases required for large projects, not consistently applied"),
                    (4, "Formal ROI framework applied consistently to AI investments"),
                    (5, "Comprehensive AI investment framework with real-time benefits realisation tracking"),
                ],
            },
        ],
    },

    3: {
        "title": "Organisational Capability & Culture",
        "icon": "🏗️",
        "questions": [
            {
                "id": "p3_q1",
                "text": "What proportion of your workforce has received foundational AI literacy training?",
                "weight": 1.2,
                "options": [
                    (1, "Less than 5% of the workforce"),
                    (2, "5–20% — mainly technical staff"),
                    (3, "20–50% — technical and some management roles"),
                    (4, "50–80% — broad coverage across most roles"),
                    (5, "Over 80% — near-universal coverage with an ongoing programme"),
                ],
            },
            {
                "id": "p3_q2",
                "text": "Is there a structured AI upskilling / reskilling programme for employees?",
                "weight": 1.3,
                "options": [
                    (1, "No programme — employees self-direct their own AI learning"),
                    (2, "Access to generic online courses only (e.g., Coursera, LinkedIn)"),
                    (3, "Structured programme for technical staff only"),
                    (4, "Broad programme covering technical and non-technical roles"),
                    (5, "Comprehensive multi-tier programme with certification and AI career pathways"),
                ],
            },
            {
                "id": "p3_q3",
                "text": "How would you rate psychological safety to experiment with AI (fail-fast culture)?",
                "weight": 1.2,
                "options": [
                    (1, "Very low — failure is penalised; no one wants to be the AI sponsor"),
                    (2, "Low — limited tolerance for experimentation, risk-aversion dominates"),
                    (3, "Moderate — some teams encouraged to experiment with AI"),
                    (4, "High — experimentation encouraged and celebrated across the organisation"),
                    (5, "Exemplary — structured innovation with protected budget and fast-fail methodology"),
                ],
            },
            {
                "id": "p3_q4",
                "text": "Does your organisation have an AI Centre of Excellence (CoE) or equivalent capability hub?",
                "weight": 1.0,
                "options": [
                    (1, "No CoE or shared AI capability exists"),
                    (2, "Informal community of practice with no mandate or funding"),
                    (3, "Small dedicated AI team without formal CoE structure"),
                    (4, "Established CoE with business engagement model and delivery mandate"),
                    (5, "Mature CoE with federated model — embedded AI roles in every business unit"),
                ],
            },
            {
                "id": "p3_q5",
                "text": "How effectively does your organisation manage the human change from AI adoption?",
                "weight": 1.3,
                "options": [
                    (1, "No change management — AI deployed without people consideration"),
                    (2, "Basic communications plans only — announce and hope"),
                    (3, "Structured change management for major AI deployments"),
                    (4, "Proactive change management with stakeholder engagement and feedback loops"),
                    (5, "Mature change and adoption practice with measurable adoption KPIs per deployment"),
                ],
            },
        ],
    },

    4: {
        "title": "Responsible AI Governance",
        "icon": "⚖️",
        "questions": [
            {
                "id": "p4_q1",
                "text": "Does your organisation have a documented and formally adopted AI Ethics Policy?",
                "weight": 1.3,
                "options": [
                    (1, "No AI ethics policy of any kind"),
                    (2, "General IT ethics policy referenced for AI — not AI-specific"),
                    (3, "AI ethics policy drafted but not formally adopted or enforced"),
                    (4, "Formal policy adopted, communicated and referenced in AI projects"),
                    (5, "Comprehensive, publicly committed policy with annual board review"),
                ],
            },
            {
                "id": "p4_q2",
                "text": "Is there a systematic process for detecting and mitigating bias in AI models and data?",
                "weight": 1.4,
                "options": [
                    (1, "No bias detection or consideration in AI development"),
                    (2, "Ad hoc reviews only when issues are raised"),
                    (3, "Basic bias testing for the highest-risk models only"),
                    (4, "Structured bias assessment integrated into the AI development lifecycle"),
                    (5, "Automated bias monitoring with continuous fairness metrics and full audit trail"),
                ],
            },
            {
                "id": "p4_q3",
                "text": "How mature is your AI regulatory compliance framework (e.g., EU AI Act, GDPR, sector rules)?",
                "weight": 1.3,
                "options": [
                    (1, "No awareness or tracking of AI-specific regulations"),
                    (2, "Aware of key regulations but no formal compliance programme"),
                    (3, "Compliance activities underway for the most critical regulations"),
                    (4, "Comprehensive compliance programme covering all relevant AI regulations"),
                    (5, "Leading practice — proactive regulatory engagement, ahead of requirements"),
                ],
            },
            {
                "id": "p4_q4",
                "text": "Is there board-level oversight and clear accountability for AI risk?",
                "weight": 1.2,
                "options": [
                    (1, "No board visibility of AI risk whatsoever"),
                    (2, "AI risk mentioned generically in annual risk reports"),
                    (3, "Board receives periodic (quarterly or annual) AI risk updates"),
                    (4, "Board committee with explicit AI risk oversight mandate"),
                    (5, "Dedicated board AI governance structure with named accountability"),
                ],
            },
            {
                "id": "p4_q5",
                "text": "Does your organisation apply data privacy principles specifically to AI systems?",
                "weight": 0.8,
                "options": [
                    (1, "No AI-specific data privacy consideration — general policy applied blindly"),
                    (2, "Standard GDPR compliance extended to AI without AI-specific controls"),
                    (3, "AI data privacy guidelines documented and referenced in projects"),
                    (4, "Formal AI privacy framework with data minimisation and consent controls"),
                    (5, "Privacy-by-design embedded in all AI development with third-party audits"),
                ],
            },
        ],
    },
}

# Convenience: flat list of all question IDs
ALL_QUESTION_IDS: List[str] = [
    q["id"]
    for p_num in sorted(PILLAR_QUESTIONS)
    for q in PILLAR_QUESTIONS[p_num]["questions"]
]



# ---------------------------------------------------------------------------
# Industry-Specific Question Banks  (12 industries × 4 pillars × 5 questions)
# ---------------------------------------------------------------------------
# IDs use format  p{pillar}_{ind_key}_{n}  where ind_key is a short slug.
# All inherit the same pillar title/icon from PILLAR_QUESTIONS for display.

_IND_QUESTIONS: Dict[str, Dict[int, List[dict]]] = {

    # ── Banking & Financial Services ────────────────────────────────────────
    "Banking and financial services": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": True,
             "text": "Does your bank's C-suite have a formally documented AI strategy aligned to regulatory expectations (e.g., EBA, Basel risk appetite)?",
             "options": [(1,"No AI strategy — regulatory or otherwise"),(2,"Informal internal discussions, nothing board-approved"),(3,"Strategy draft exists but is not formally adopted"),(4,"Board-approved AI strategy with regulatory mapping"),(5,"Comprehensive AI strategy, externally communicated and integrated into ICAAP/ILAAP")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the bank's ExCo or Risk Committee formally review AI transformation and model risk progress?",
             "options": [(1,"Never — only ad hoc when a model failure occurs"),(2,"Annually in the risk review cycle"),(3,"Quarterly — structured management information pack"),(4,"Monthly — dedicated AI and model risk standing agenda item"),(5,"Continuous — AI risk dashboard integrated into real-time governance reporting")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Chief AI/Data Officer or AI Risk Executive with explicit mandate and P&L accountability?",
             "options": [(1,"No dedicated role exists"),(2,"AI is a secondary responsibility within CTO/CRO"),(3,"Named lead but with constrained authority and no direct budget"),(4,"CAIO/CDO appointed with defined mandate and budget"),(5,"C-suite AI executive with board access, regulatory liaison remit, and transformation P&L")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate executive literacy on AI model risk, algorithmic bias, and regulatory expectations (SR 11-7, EU AI Act)?",
             "options": [(1,"Very low — AI model risk not understood at ExCo level"),(2,"Basic awareness — executives defer entirely to quants/IT"),(3,"Moderate — key model risk concepts understood, regulators' expectations referenced"),(4,"Strong — executives actively engaged in model risk governance forums"),(5,"Exemplary — executives personally drive responsible AI agenda with regulators")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does the board visibly champion AI ethics, explainability, and customer fairness as strategic priorities?",
             "options": [(1,"No visible board position on AI ethics"),(2,"Included in CSR statements only"),(3,"AI fairness mentioned in risk appetite statement"),(4,"Board actively reviews AI fairness metrics and complaints data"),(5,"Board has a published responsible AI charter with named trustee accountability")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": True,
             "text": "Are bank AI initiatives directly tied to measurable financial outcomes — NIM improvement, credit loss reduction, cost-to-income ratio?",
             "options": [(1,"No financial KPIs defined for any AI project"),(2,"High-level references to efficiency — not tracked"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked financial business cases"),(5,"All AI investments governed by real-time financial ROI dashboards reviewed at ExCo")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is your Model Risk Management (MRM) framework for governing AI model development, validation, and retirement?",
             "options": [(1,"No MRM framework — models approved ad hoc"),(2,"Basic model inventory exists, no formal validation process"),(3,"MRM policy documented; validation applied to high-risk models only"),(4,"Full MRM lifecycle with independent validation and model risk appetite"),(5,"Leading MRM practice — automated model monitoring, risk tiering, and regulatory audit trail")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do business lines and technology collaborate on AI solutions — with shared outcome ownership?",
             "options": [(1,"Completely siloed — business throws requirements over the wall"),(2,"Limited joint design — mostly at requirements sign-off"),(3,"Joint squads for flagship projects only"),(4,"Embedded product owners from business in AI delivery teams"),(5,"Full co-ownership — AI P&L attributed jointly to business and technology leads")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the technology roadmap explicitly prioritise AI use cases tied to the bank's strategic plan (e.g., digital lending, fraud, AML)?",
             "options": [(1,"Technology roadmap is IT-led with no business strategy input"),(2,"Some AI use cases referenced but not prioritised"),(3,"Priority use cases mapped to strategy but not formally governed"),(4,"AI portfolio governed with strategy alignment review at quarterly ExCo"),(5,"Real-time portfolio rebalancing with direct traceability to strategic objectives")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal benefits realisation framework tracking the financial and risk impact of deployed AI models?",
             "options": [(1,"No post-deployment tracking whatsoever"),(2,"Anecdotal benefit reporting at project close"),(3,"Business cases reviewed at 6 months post-go-live only"),(4,"Formal benefits tracking with quarterly ExCo reporting"),(5,"Continuous AI value attribution with automated financial reconciliation")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of your banking workforce (including branch, operations, risk) has received foundational AI and data literacy training?",
             "options": [(1,"<5% — only specialist technical staff"),(2,"5–20% — mainly quants, data scientists, IT"),(3,"20–50% — technical, some risk and compliance"),(4,"50–80% — broad coverage including front-line and risk teams"),(5,">80% — near-universal with mandatory AI literacy as part of induction")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI upskilling programme covering both technical AI skills and responsible AI / model risk awareness?",
             "options": [(1,"No programme — self-directed learning only"),(2,"Access to generic online courses (Coursera, LinkedIn) only"),(3,"Structured programme for technical staff; nothing for risk/compliance/business"),(4,"Broad programme covering data science, model risk, and AI ethics"),(5,"Multi-tier certification programme with AI career pathways for all functions including RM, compliance, and front-line")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How would you rate psychological safety to challenge AI model outputs and escalate concerns within the bank?",
             "options": [(1,"Very low — model outputs are accepted without question"),(2,"Low — challenge is informal and discouraged"),(3,"Moderate — model challenge process exists for high-risk models"),(4,"High — formal model challenge embedded in validation and governance"),(5,"Exemplary — structured red-team challenges and independent model review panels")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the bank have an AI/Data Centre of Excellence with mandate to govern model standards and upskill the organisation?",
             "options": [(1,"No CoE or shared AI capability"),(2,"Informal group with no budget or governance mandate"),(3,"Small central data science team — no formal CoE structure"),(4,"Established CoE with MRM standards ownership and business engagement"),(5,"Mature federated CoE with embedded AI roles across all business lines and risk functions")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the bank manage workforce change from AI automation (e.g., credit decisioning, AML screening, customer service)?",
             "options": [(1,"No change management — automation deployed without staff engagement"),(2,"Communication-only approach — announcement and move on"),(3,"Structured change management for major AI deployments"),(4,"Proactive reskilling programme aligned to automation roadmap"),(5,"Comprehensive workforce transition strategy with union/works council engagement and redeployment guarantees")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the bank have a formally adopted Responsible AI / AI Ethics Policy covering explainability, fairness, and customer harm prevention?",
             "options": [(1,"No AI ethics policy — general IT policy applied"),(2,"Draft policy exists but is not board-approved"),(3,"Policy adopted internally but not communicated to customers or regulators"),(4,"Board-approved policy with public commitment and annual review"),(5,"Comprehensive published charter with independent ethics advisory board and regulatory engagement")]},
            {"id": "p4_q2", "weight": 1.4, "critical": True,
             "text": "Is there a systematic process for detecting and mitigating algorithmic bias in credit, pricing, and customer-facing AI models?",
             "options": [(1,"No bias testing — models deployed without fairness checks"),(2,"Ad hoc review when bias complaints are received"),(3,"Basic disparity testing for highest-risk models only (e.g., mortgage decisioning)"),(4,"Structured fairness assessment integrated into model development and validation lifecycle"),(5,"Automated continuous bias monitoring with real-time fairness dashboards and regulatory disclosure")]},
            {"id": "p4_q3", "weight": 1.3, "critical": True,
             "text": "How mature is the bank's AI regulatory compliance programme — covering EU AI Act, SR 11-7, GDPR, Consumer Duty, and sector-specific AI rules?",
             "options": [(1,"No awareness of AI-specific regulations"),(2,"Aware of key rules but no formal compliance programme"),(3,"Compliance activities underway for most critical regulations"),(4,"Comprehensive compliance programme with regulatory horizon scanning"),(5,"Leading practice — proactive regulator engagement and ahead of all compliance requirements")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Board Risk Committee oversight with named accountable executive for AI risk (including model risk, third-party AI, and algorithmic conduct risk)?",
             "options": [(1,"No board visibility of AI risk"),(2,"AI risk mentioned generically in annual risk report"),(3,"Board receives periodic AI risk briefings"),(4,"Board Risk Committee has explicit AI risk oversight mandate"),(5,"Dedicated board AI governance structure with CRO/CAIO joint accountability and external audit")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the bank apply data privacy-by-design to all AI systems, including third-party AI model data flows?",
             "options": [(1,"No AI-specific data privacy controls — general GDPR compliance applied"),(2,"Standard GDPR extended to AI without AI-specific controls"),(3,"AI data privacy guidelines documented and referenced in projects"),(4,"Formal AI privacy framework with data minimisation and consent architecture"),(5,"Privacy-by-design embedded in all AI development with third-party audits and ICO engagement")]},
        ],
    },

    # ── Healthcare & Hospital Administration ────────────────────────────────
    "Healthcare and hospital administration": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does hospital/health system leadership have a formally documented AI clinical and operational strategy endorsed by the Chief Medical Officer?",
             "options": [(1,"No AI strategy exists"),(2,"Informal pilot discussions only"),(3,"Strategy draft in development with no clinical sign-off"),(4,"Documented strategy endorsed by CMO/CEO"),(5,"Comprehensive AI strategy integrated into clinical governance and quality improvement frameworks")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the hospital's clinical leadership board formally review AI deployment safety and patient outcome impact?",
             "options": [(1,"Never — only if a patient safety incident occurs"),(2,"Annually in quality review"),(3,"Quarterly with clinical governance committee"),(4,"Monthly via patient safety and technology board"),(5,"Continuous real-time monitoring with weekly clinical AI safety review")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Chief Clinical Information Officer (CCIO) or AI Patient Safety Lead with authority over clinical AI deployments?",
             "options": [(1,"No clinical AI leadership role exists"),(2,"IT leads AI with no clinical authority"),(3,"CCIO exists but with limited mandate over AI systems"),(4,"CCIO with formal clinical AI oversight remit"),(5,"Empowered Chief AI Officer with CMO joint-accountability for all clinical AI decisions")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate clinical leadership AI literacy — understanding AI limitations, failure modes, and appropriate use in clinical workflows?",
             "options": [(1,"Very low — clinicians treat AI as a black box oracle"),(2,"Basic — clinicians aware AI exists but not how it fails"),(3,"Moderate — senior clinicians understand key risks of AI in their specialty"),(4,"Strong — clinical leadership actively questions and validates AI recommendations"),(5,"Exemplary — clinicians co-design AI safety protocols and participate in model validation")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does the Board of Directors / Trust Board visibly champion responsible AI adoption as a patient safety priority?",
             "options": [(1,"No visible board position on AI"),(2,"AI mentioned in digital strategy documents only"),(3,"Board receives annual AI progress update"),(4,"Board has AI as standing governance agenda item with patient safety lens"),(5,"Board-level AI ethics committee with patient/carer representation and external clinical expert membership")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are healthcare AI initiatives tied to measurable patient outcome KPIs — readmission rates, diagnostic accuracy, waiting time reduction?",
             "options": [(1,"No patient outcome KPIs defined for any AI project"),(2,"Vague references to 'improving care' without metrics"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked clinical outcome metrics"),(5,"All AI investments governed by real-time clinical outcome dashboards reviewed at board level")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the clinical validation and health technology assessment (HTA) process for AI medical devices and clinical decision support?",
             "options": [(1,"No formal clinical validation — AI deployed based on vendor claims"),(2,"Basic clinical review by a single clinician"),(3,"HTA process applied to highest-risk AI tools only"),(4,"Formal multi-disciplinary clinical validation required for all patient-facing AI"),(5,"NICE/CE-mark equivalent validation with post-market surveillance and real-world evidence generation")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effective is collaboration between clinical staff, informatics, and technology teams in designing AI-supported care pathways?",
             "options": [(1,"Completely siloed — technology builds, clinicians receive"),(2,"Clinicians consulted at end of build only"),(3,"Some joint working in design but significant friction"),(4,"Clinical co-design embedded in all AI product development"),(5,"Fully integrated clinical-technology squads with shared patient outcome accountability")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the digital and technology roadmap directly support clinical strategy priorities — elective recovery, prevention, integrated care?",
             "options": [(1,"Technology roadmap built independently of clinical priorities"),(2,"Partial alignment reviewed in annual planning"),(3,"AI roadmap mapped to clinical priorities but not formally governed"),(4,"Technology roadmap co-developed with clinical leadership"),(5,"Real-time clinical-technology strategy alignment with integrated care system governance")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal business case and clinical benefit realisation framework for healthcare AI investments?",
             "options": [(1,"No formal business case — AI approved based on vendor pitch"),(2,"Cost justification only — no clinical benefit tracking"),(3,"Business cases required for large projects; not consistently applied"),(4,"Formal clinical ROI framework applied to all AI investments"),(5,"Comprehensive AI investment framework with real-world clinical evidence generation and QALY assessment")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of clinical and administrative staff have received foundational AI literacy training specific to healthcare AI risks?",
             "options": [(1,"<5% — only data/IT specialists"),(2,"5–20% — mainly informatics and digital staff"),(3,"20–50% — technical and some senior clinicians"),(4,"50–80% — broad coverage including nursing and allied health"),(5,">80% — universal coverage with role-specific AI safety modules for all clinical staff")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured clinical AI upskilling programme covering both digital skills and safe AI use in clinical decision-making?",
             "options": [(1,"No programme — clinicians self-direct learning"),(2,"Access to generic online courses only"),(3,"Structured programme for informatics staff only"),(4,"Broad programme covering clinical, nursing, and administrative roles"),(5,"Comprehensive multi-tier programme with clinical simulation, AI safety modules, and CPD accreditation")]},
            {"id": "p3_q3", "weight": 1.2, "critical": True,
             "text": "How strong is the culture of clinical oversight and human-in-the-loop governance for AI recommendations in patient care?",
             "options": [(1,"AI recommendations followed without clinical review — dangerous dependency"),(2,"Informal norm to check AI output but no formal protocol"),(3,"Human override required for high-risk AI recommendations only"),(4,"Formal clinical human-in-the-loop protocol for all patient-facing AI"),(5,"Structured clinical accountability framework — AI is advisory only, clinician retains full accountability with audit trail")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have a Clinical AI Centre of Excellence or Health Informatics hub driving standards and best practice?",
             "options": [(1,"No clinical AI capability hub exists"),(2,"Informal clinical informatics community with no mandate"),(3,"Small digital health team without CoE structure"),(4,"Established Clinical AI CoE with governance mandate and clinical engagement"),(5,"Mature Clinical AI CoE with federated model — embedded digital health roles in each clinical directorate")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage workforce change from clinical AI adoption — including staff concerns about deskilling and job security?",
             "options": [(1,"No change management — AI deployed without staff consultation"),(2,"Staff briefings only — no structured engagement"),(3,"Structured change management for major AI deployments"),(4,"Proactive engagement with clinical unions and staff side on AI roadmap"),(5,"Comprehensive clinical workforce strategy with reskilling commitments and professional body engagement"),(5,"Comprehensive workforce strategy with redeployment pathways and union agreement")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": True,
             "text": "Does the organisation have a formally adopted AI Ethics and Patient Safety Policy covering clinical AI risk classification and ethics committee review?",
             "options": [(1,"No AI ethics policy — general clinical governance applied"),(2,"General data governance policy referenced for AI"),(3,"AI ethics policy drafted but not formally adopted by board"),(4,"Board-adopted AI ethics policy with ethics committee review for patient-facing AI"),(5,"Comprehensive publicly committed policy with independent clinical AI ethics board and patient representative involvement")]},
            {"id": "p4_q2", "weight": 1.4, "critical": True,
             "text": "Is there a systematic process for detecting and mitigating AI bias in clinical decision support tools (e.g., across demographics, ethnicity, comorbidities)?",
             "options": [(1,"No bias testing — tools deployed based on vendor evidence only"),(2,"Ad hoc clinical review when bias concerns are raised"),(3,"Basic disparity analysis for highest-risk clinical AI tools"),(4,"Structured fairness assessment across demographics integrated into clinical validation"),(5,"Automated post-deployment bias monitoring with disaggregated outcome reporting and MHRA disclosure")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the regulatory compliance framework for AI as a medical device (AIMD) — covering UKCA/CE marking, MHRA, NHS DTAC?",
             "options": [(1,"No awareness of AIMD regulatory requirements"),(2,"Aware of regulations but no formal compliance programme"),(3,"Compliance activities underway for highest-risk clinical AI tools"),(4,"Comprehensive compliance programme covering AIMD, DTAC, and data protection"),(5,"Leading practice — proactive MHRA engagement, horizon scanning, and ahead of all requirements")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Trust Board / Board of Directors oversight with named clinical accountability (e.g., Medical Director) for AI patient safety risk?",
             "options": [(1,"No board visibility of AI patient safety risk"),(2,"AI mentioned in digital transformation board papers only"),(3,"Board receives periodic (quarterly/annual) AI safety briefings"),(4,"Board committee with explicit AI patient safety oversight mandate"),(5,"Dedicated board clinical AI governance structure with Medical Director accountability and CQC engagement")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply data minimisation and patient consent principles specifically to AI model training and clinical data sharing?",
             "options": [(1,"No AI-specific consent or data minimisation controls"),(2,"Standard Caldicott/GDPR applied without AI-specific safeguards"),(3,"AI data governance guidelines documented and referenced in projects"),(4,"Formal AI data governance with explicit patient consent architecture and IG sign-off"),(5,"Privacy-by-design in all AI development with ICO engagement and patient data charter")]},
        ],
    },

    # ── Manufacturing & Plant Operations ────────────────────────────────────
    "Manufacturing and plant operations": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does plant and manufacturing leadership have a documented Industry 4.0 / AI vision endorsed at board level and integrated into the capital investment plan?",
             "options": [(1,"No AI or Industry 4.0 strategy"),(2,"Informal pilot discussions in engineering only"),(3,"Strategy draft in development — not board-endorsed"),(4,"Board-endorsed AI/Industry 4.0 vision with capital allocation"),(5,"Comprehensive AI strategy integrated into manufacturing excellence roadmap and 5-year CapEx plan")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the Plant Director / Operations Board formally review AI and automation transformation progress against production KPIs?",
             "options": [(1,"Never — only when a production incident occurs"),(2,"Annually in the operations review"),(3,"Quarterly — structured operations board reviews"),(4,"Monthly — AI/automation as standing agenda item at operations board"),(5,"Continuous — real-time OEE and AI performance dashboards reviewed weekly by plant leadership")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Digital Manufacturing / Industry 4.0 leader with authority over AI adoption, OT/IT integration, and automation investments?",
             "options": [(1,"No dedicated role — AI driven by individual engineers"),(2,"AI responsibility split between IT and engineering informally"),(3,"Part-time digital lead with limited budget authority"),(4,"Dedicated Head of Digital Manufacturing with engineering and IT mandate"),(5,"Chief Digital/Manufacturing Officer with board access, CapEx authority, and OT security remit")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate operations and plant leadership AI literacy — understanding AI-driven predictive maintenance, quality control, and supply chain optimisation?",
             "options": [(1,"Very low — plant leaders see AI as an IT project"),(2,"Basic awareness — engineering teams understand concepts, leadership does not"),(3,"Moderate — operations leadership understands key AI use cases and their limitations"),(4,"Strong — plant leadership actively engages with AI vendors and benchmarks"),(5,"Exemplary — leadership drives AI manufacturing strategy, participates in industry consortia")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does senior leadership visibly champion AI as a manufacturing competitiveness and safety priority — not merely a cost-reduction tool?",
             "options": [(1,"No visible leadership on AI beyond cost-cutting"),(2,"AI referenced in annual report only"),(3,"Occasional public commitment to digital manufacturing"),(4,"Regular leadership communication on AI as a strategic and safety priority"),(5,"CEO-endorsed AI manufacturing programme with published targets for OEE, safety, and sustainability impact")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": True,
             "text": "Are manufacturing AI initiatives directly tied to measurable production KPIs — OEE, scrap rate, MTTR, on-time delivery — with formal targets?",
             "options": [(1,"No production KPIs defined for any AI project"),(2,"Vague 'efficiency improvement' goals without measurement"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked production business cases"),(5,"All AI investments governed by real-time OEE and operational KPI dashboards reviewed at plant board")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the AI portfolio governance process across your manufacturing and supply chain operations?",
             "options": [(1,"No formal process — AI projects approved ad hoc by engineering"),(2,"Informal prioritisation driven by IT or individual plant managers"),(3,"Basic portfolio tracking with some operations leadership input"),(4,"Formal AI portfolio governance with CapEx business case and stage-gate reviews"),(5,"Mature portfolio management with ROI tracking, technology readiness assessment, and dynamic rebalancing")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do operations, engineering, IT, and OT teams collaborate on AI and automation deployments — with shared accountability for production outcomes?",
             "options": [(1,"Completely siloed — IT deploys, engineering complains"),(2,"Limited collaboration at system integration boundary only"),(3,"Some joint working exists but OT/IT friction remains significant"),(4,"Integrated OT/IT teams with shared production KPI ownership"),(5,"Fully integrated cross-functional squads with co-ownership of uptime, quality, and safety outcomes")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the manufacturing technology roadmap explicitly prioritise AI use cases mapped to competitive strategy — localisation, nearshoring, sustainability, quality leadership?",
             "options": [(1,"Technology roadmap built independently of competitive strategy"),(2,"Some AI use cases referenced but not formally prioritised"),(3,"AI roadmap mapped to strategy but governed informally"),(4,"Technology roadmap co-developed with commercial and operations leadership"),(5,"Real-time strategy-technology alignment with OEM/Tier-1 ecosystem co-development")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal ROI and payback framework applied to all manufacturing AI and automation investments?",
             "options": [(1,"No formal ROI process — investments approved on engineering intuition"),(2,"Basic payback period calculation only — no post-deployment tracking"),(3,"Business cases required for large investments — inconsistently applied"),(4,"Formal ROI framework applied consistently with 12-month post-deployment review"),(5,"Comprehensive AI investment framework with real-time production value attribution and CapEx rebalancing")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of your manufacturing workforce — including operators, technicians, and engineers — has received AI and automation literacy training?",
             "options": [(1,"<5% — only data/IT engineers"),(2,"5–20% — mainly engineers and maintenance technicians"),(3,"20–50% — technical staff and some shift supervisors"),(4,"50–80% — broad coverage including operators and quality teams"),(5,">80% — near-universal with role-specific AI/automation modules for all plant roles")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured upskilling programme covering AI-driven predictive maintenance, quality vision systems, and cobotic operation for shop floor employees?",
             "options": [(1,"No programme — operators self-direct learning"),(2,"Generic digital skills courses only — not manufacturing-specific"),(3,"Structured programme for engineers only"),(4,"Broad programme covering operators, technicians, and quality teams"),(5,"Comprehensive multi-tier programme with simulation, cobotic training, and recognised manufacturing qualifications")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of questioning and validating AI/automation recommendations before implementing physical changes on the plant floor?",
             "options": [(1,"Very low — machine recommendations executed without human validation"),(2,"Informal norm to check output but no formal protocol"),(3,"Human validation required for high-risk automated decisions only"),(4,"Formal human-in-the-loop protocol for all safety-critical AI/automation actions"),(5,"Structured human-machine teaming framework with permit-to-work integration and audit trail")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have a Digital Manufacturing / Industry 4.0 Centre of Excellence driving AI standards across plants?",
             "options": [(1,"No CoE or shared digital manufacturing capability"),(2,"Informal engineering community with no mandate or funding"),(3,"Small central team without formal CoE structure"),(4,"Established CoE with manufacturing standards ownership and plant engagement model"),(5,"Mature federated CoE with embedded digital manufacturing engineers in each plant and supply chain partners")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage workforce change from AI and automation — including operator role redesign and retraining for augmented roles?",
             "options": [(1,"No change management — automation deployed without workforce planning"),(2,"Communication only — announce new system and move on"),(3,"Structured change management for major automation deployments"),(4,"Proactive reskilling aligned to automation roadmap with union/works council engagement"),(5,"Comprehensive workforce transformation strategy with redeployment guarantees and employee involvement in automation design")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the organisation have an AI and Automation Safety Policy covering OT cybersecurity, functional safety (ISO 13849/IEC 62061), and AI system safety assessment?",
             "options": [(1,"No AI/automation safety policy — general H&S policy applied"),(2,"General machinery safety policy referenced for AI systems"),(3,"AI safety policy drafted but not formally adopted"),(4,"Formally adopted AI safety policy with functional safety assessment requirements"),(5,"Comprehensive AI safety governance framework with OT cybersecurity, IEC 62443 compliance, and independent safety case review")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a systematic process for validating AI model outputs before they trigger physical production actions — to prevent scrap, machine damage, or safety incidents?",
             "options": [(1,"No validation — AI outputs trigger physical actions automatically"),(2,"Ad hoc review when a production incident occurs"),(3,"Validation for highest-risk automated actions only"),(4,"Structured human engineering sign-off before AI-triggered physical actions"),(5,"Formal safety case process with fault tree analysis and SIL assessment for all safety-critical AI actions")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the AI regulatory compliance framework — covering EU AI Act high-risk AI (industrial safety), machinery regulation, and product liability?",
             "options": [(1,"No awareness of AI-specific manufacturing regulations"),(2,"Aware of key rules but no formal compliance programme"),(3,"Compliance activities for most critical regulations underway"),(4,"Comprehensive compliance programme with regulatory horizon scanning"),(5,"Leading practice — regulatory pre-engagement and type-examination for AI-integrated machinery")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there board-level oversight with named accountability for AI and OT cyber risk — including supply chain AI risk?",
             "options": [(1,"No board visibility of AI or OT risk"),(2,"AI/OT risk mentioned generically in risk register"),(3,"Board receives periodic AI and OT risk briefings"),(4,"Board committee with explicit AI/OT risk oversight mandate"),(5,"Dedicated board structure for AI and OT governance with CISO/COO joint accountability")]},
            {"id": "p4_q5", "weight": 0.8, "critical": True,
             "text": "Does the organisation apply data security and IP protection principles specifically to AI training data from production systems and supplier data?",
             "options": [(1,"No AI-specific data security — general IT policy applied to OT"),(2,"Standard IT security extended to OT data without AI-specific controls"),(3,"AI data governance policy documented but not consistently applied to production data"),(4,"Formal AI data governance with OT data classification and supplier data controls"),(5,"Comprehensive AI IP protection framework with data sovereignty controls and supply chain audit rights")]},
        ],
    },

    # ── IT Services & Service Desk ───────────────────────────────────────────
    "IT services and service desk operations": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does IT leadership have a formally documented AI strategy for service desk transformation — covering ticket deflection, self-service, and agent augmentation?",
             "options": [(1,"No AI strategy for IT service management"),(2,"Informal discussions about chatbots only"),(3,"Strategy draft in development with no CIO endorsement"),(4,"CIO-endorsed AI strategy with service desk KPI targets"),(5,"Board-endorsed AI strategy with CSAT, MTTR, and deflection rate targets integrated into IT scorecard")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does IT leadership formally review AI service desk transformation progress against service quality and cost KPIs?",
             "options": [(1,"Never — only when an AI incident occurs"),(2,"Annually in IT strategy review"),(3,"Quarterly structured reviews"),(4,"Monthly — AI service performance as standing agenda item"),(5,"Continuous real-time dashboards reviewed weekly by IT leadership with business sponsors")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated AI/Automation Lead for IT Service Management with authority over tool selection, ITSM integration, and service quality?",
             "options": [(1,"No dedicated lead — AI decided by individual service desk managers"),(2,"AI is a secondary responsibility within IT Operations"),(3,"Named lead but with no budget authority or ITSM governance mandate"),(4,"Dedicated ITSM AI lead with tool selection and integration authority"),(5,"Head of Intelligent Automation with board-level IT scorecard accountability")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate IT leadership AI literacy — understanding AI's role in AIOps, ITSM automation, and service quality improvement?",
             "options": [(1,"Very low — IT leaders see AI as vendor marketing"),(2,"Basic — aware of chatbots and virtual agents only"),(3,"Moderate — understand AIOps, knowledge management AI, and predictive alerting"),(4,"Strong — IT leadership actively drives AI ITSM roadmap decisions"),(5,"Exemplary — IT leadership benchmarks against leading ITSM AI maturity and co-develops with vendors")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does IT leadership visibly champion AI as a service quality and agent experience priority — not just a cost-reduction lever?",
             "options": [(1,"No visible leadership on AI beyond headcount reduction"),(2,"AI referenced in IT cost-saving plans only"),(3,"Occasional public commitment to digital service quality"),(4,"Regular IT leadership communication on AI as a service improvement priority"),(5,"CIO-endorsed AI service excellence programme with published user satisfaction and agent wellbeing targets")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": True,
             "text": "Are IT AI investments directly tied to measurable service KPIs — ticket deflection rate, CSAT, MTTR, first-call resolution, and cost-per-ticket?",
             "options": [(1,"No service KPIs defined for any AI project"),(2,"Vague 'efficiency improvement' goals without measurement"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked service KPI business cases"),(5,"All AI investments governed by real-time service dashboards reviewed by IT and business leaders weekly")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the IT AI portfolio governance process — covering prioritisation of ITSM AI, AIOps, and intelligent automation investments?",
             "options": [(1,"No formal process — tools selected by individual service desk managers"),(2,"Informal prioritisation driven by helpdesk vendor relationships"),(3,"Basic tracking with some IT leadership input"),(4,"Formal AI portfolio governance with business case and service KPI gates"),(5,"Mature portfolio management with ROI tracking, tool consolidation strategy, and dynamic rebalancing")]},
            {"id": "p2_q3", "weight": 1.3, "critical": True,
             "text": "How effectively do IT service teams and business stakeholders collaborate on AI tool design — ensuring AI self-service matches real user needs?",
             "options": [(1,"Completely siloed — IT builds chatbots, users reject them"),(2,"Business consulted at UAT only"),(3,"Some joint design workshops but significant friction"),(4,"Co-design with business service owners embedded in AI product development"),(5,"Fully integrated IT-business squads with shared CSAT and deflection rate accountability")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the IT technology roadmap explicitly prioritise ITSM AI, AIOps, and intelligent automation aligned to business digital transformation goals?",
             "options": [(1,"Technology roadmap built independently of business strategy"),(2,"Some AI tools referenced but not formally prioritised"),(3,"ITSM AI roadmap mapped to business priorities but governed informally"),(4,"IT roadmap co-developed with business leadership with ITSM AI as a priority workstream"),(5,"Real-time IT-business strategy alignment with intelligent automation as a shared digital platform")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal ROI and user adoption framework tracking AI value in service desk operations?",
             "options": [(1,"No post-deployment tracking — tool purchased and forgotten"),(2,"Anecdotal benefit reporting at project close"),(3,"Ticket deflection tracked at 6 months post-go-live only"),(4,"Formal benefits tracking with quarterly IT leadership reporting"),(5,"Continuous AI value attribution with real-time service KPI reconciliation and user adoption analytics")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of IT service desk agents and IT operations staff have received training on AI tools — including virtual agents, AIOps platforms, and automation?",
             "options": [(1,"<5% — only tool admins"),(2,"5–20% — mainly platform specialists"),(3,"20–50% — technical staff and some team leaders"),(4,"50–80% — broad agent and operations coverage"),(5,">80% — universal coverage with role-specific AI augmentation training for all service desk staff")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured upskilling programme for service desk agents on working alongside AI — including prompt engineering, escalation judgment, and AI output validation?",
             "options": [(1,"No programme — agents left to discover AI tools themselves"),(2,"Generic vendor training only"),(3,"Structured programme for AI tool admins only"),(4,"Broad programme covering agents, team leaders, and service managers"),(5,"Comprehensive multi-tier programme with AI augmentation skills, judgment training, and ITSM certification integration")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of agents critically evaluating AI suggestions rather than blindly following AI-recommended resolutions?",
             "options": [(1,"Very low — agents accept AI suggestions without review, causing errors"),(2,"Informal — some agents check, most do not"),(3,"Moderate — team leaders encourage AI output review for complex tickets"),(4,"High — formal AI output validation protocol for all customer-facing resolutions"),(5,"Exemplary — structured agent-AI teaming framework with quality assurance and feedback loop into AI training")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the IT organisation have an Intelligent Automation or AIOps Centre of Excellence driving tool standards and best practice?",
             "options": [(1,"No CoE — each service team buys its own tools"),(2,"Informal community of practice with no mandate"),(3,"Small central automation team without CoE structure"),(4,"Established CoE with ITSM AI governance and business engagement model"),(5,"Mature CoE with federated model — embedded AI automation engineers in each IT service tower")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does IT manage the human change from AI-driven service desk transformation — including agent role redesign and wellbeing?",
             "options": [(1,"No change management — AI deployed without agent engagement"),(2,"Email announcement only"),(3,"Structured change management for major AI deployments"),(4,"Proactive agent engagement with role redesign and redeployment planning"),(5,"Comprehensive workforce strategy with agent co-design of AI tools, wellbeing monitoring, and career pathway redefinition")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the IT organisation have a Responsible AI Policy for ITSM and AIOps tools — covering data privacy, user consent, and algorithmic fairness in service routing?",
             "options": [(1,"No AI ethics policy — general IT policy applied"),(2,"Vendor terms of service referenced as sufficient"),(3,"Draft AI policy exists but is not formally adopted"),(4,"Formally adopted responsible AI policy covering ITSM and AIOps"),(5,"Comprehensive published AI ethics policy with user-facing transparency statement and annual review")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a process for identifying and mitigating AI bias in service routing — e.g., AI ticket prioritisation systematically disadvantaging certain user groups?",
             "options": [(1,"No bias testing for service routing AI"),(2,"Ad hoc review when user complaints are received"),(3,"Basic disparity analysis for highest-risk service automation"),(4,"Structured fairness assessment for all user-facing AI routing and prioritisation"),(5,"Automated continuous fairness monitoring with disaggregated service level reporting by user group")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the organisation's compliance framework for AI tools used in ITSM — covering GDPR (service data), EU AI Act, and supplier AI risk management?",
             "options": [(1,"No awareness of AI-specific regulations for ITSM tools"),(2,"Aware of GDPR and EU AI Act but no formal compliance programme"),(3,"Compliance activities for most critical regulations underway"),(4,"Comprehensive compliance programme covering GDPR, EU AI Act, and supplier AI risk"),(5,"Leading practice — proactive regulatory engagement and supplier AI compliance audits")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there IT leadership / CIO oversight with named accountability for AI risk in ITSM — including third-party AI tool risk and data exposure?",
             "options": [(1,"No leadership visibility of AI risk in ITSM tools"),(2,"AI risk mentioned generically in IT risk register"),(3,"CIO receives periodic AI risk briefings"),(4,"IT risk committee with explicit AI ITSM risk oversight mandate"),(5,"CIO/CISO joint accountability for AI and data risk in all ITSM tools with third-party audit rights")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply data minimisation and user consent principles to AI models trained on service desk interaction data and employee data?",
             "options": [(1,"No AI-specific data privacy controls for service data"),(2,"Standard GDPR applied without AI-specific controls"),(3,"AI data governance guidelines documented for ITSM"),(4,"Formal AI privacy framework with data minimisation and employee consent architecture"),(5,"Privacy-by-design in all ITSM AI with DPA/ICO engagement and employee transparency statement")]},
        ],
    },

    # ── Retail & E-Commerce ─────────────────────────────────────────────────
    "Retail and e-commerce": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does retail leadership have a formally documented AI strategy aligned to customer experience, personalisation, and supply chain optimisation goals?",
             "options": [(1,"No AI strategy"),(2,"Informal e-commerce tech discussions only"),(3,"Strategy draft exists but not board-endorsed"),(4,"Board-approved AI strategy with customer experience KPI targets"),(5,"Comprehensive AI strategy integrated into commercial plan with NPS, conversion, and revenue targets")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the retail Executive Committee review AI transformation progress against commercial and customer experience KPIs?",
             "options": [(1,"Never — only if a major customer incident occurs"),(2,"Annually in commercial strategy review"),(3,"Quarterly ExCo review"),(4,"Monthly ExCo AI performance review"),(5,"Continuous real-time AI commercial dashboards with weekly ExCo stand-up")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Chief Data & AI Officer or Head of Personalisation/AI with authority over the AI commercial roadmap?",
             "options": [(1,"No dedicated role"),(2,"AI responsibility split between e-commerce and IT"),(3,"Named lead with limited budget authority"),(4,"CDAO appointed with AI commercial roadmap authority"),(5,"C-suite AI lead with P&L accountability for AI-driven revenue and margin improvement")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate retail leadership AI literacy — covering personalisation algorithms, demand forecasting, pricing AI, and customer trust?",
             "options": [(1,"Very low — retail leaders see AI as an IT topic"),(2,"Basic — aware of product recommendations only"),(3,"Moderate — leadership understands personalisation, fraud detection, and demand AI"),(4,"Strong — retail leadership actively drives AI commercial strategy"),(5,"Exemplary — leadership benchmarks AI against retail competitors and co-develops with platforms")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does senior leadership visibly champion AI as a customer trust and experience priority — not just a revenue optimisation tool?",
             "options": [(1,"No visible leadership on AI beyond conversion rate optimisation"),(2,"AI referenced in investor materials only"),(3,"Occasional public commitment to personalisation"),(4,"Regular leadership communication on AI as a customer trust priority"),(5,"CEO-endorsed AI customer charter with published commitments on personalisation transparency and data rights")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": True,
             "text": "Are retail AI investments directly tied to measurable commercial KPIs — conversion rate, basket size, NPS, customer lifetime value, and return rate reduction?",
             "options": [(1,"No commercial KPIs defined for any AI project"),(2,"Vague 'personalisation improvement' without metrics"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked commercial business cases"),(5,"All AI investments governed by real-time commercial dashboards with attribution modelling reviewed by ExCo")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the AI portfolio governance across merchandising, supply chain, pricing, and customer experience AI use cases?",
             "options": [(1,"No formal process — tools selected by individual category managers"),(2,"Informal prioritisation driven by e-commerce tech vendors"),(3,"Basic tracking with some ExCo input"),(4,"Formal AI portfolio governance with commercial business case gates"),(5,"Mature portfolio management with commercial ROI tracking, attribution, and dynamic rebalancing by season")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do commercial, digital, supply chain, and technology teams collaborate on AI solutions — with shared revenue accountability?",
             "options": [(1,"Siloed — technology builds AI, commercial teams ignore it"),(2,"Limited collaboration at product launch only"),(3,"Some joint squads for major AI projects"),(4,"Embedded commercial product owners in AI delivery teams"),(5,"Fully integrated AI squads with shared revenue, margin, and NPS accountability across commercial and technology teams")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the digital and technology roadmap explicitly prioritise AI use cases tied to commercial strategy — category growth, international expansion, omnichannel?",
             "options": [(1,"Technology roadmap built independently of commercial strategy"),(2,"Some AI tools referenced but not formally prioritised"),(3,"AI roadmap mapped to commercial strategy but governed informally"),(4,"Technology roadmap co-developed with commercial and marketing leadership"),(5,"Real-time commercial-technology strategy alignment with AI as the core digital commercial platform")]},
            {"id": "p2_q5", "weight": 1.0, "critical": True,
             "text": "Is there a formal AI value tracking framework measuring AI contribution to revenue, margin, and customer satisfaction — with attribution modelling?",
             "options": [(1,"No post-deployment value tracking"),(2,"Anecdotal revenue attribution at project close"),(3,"Basic uplift tracking at 6 months only"),(4,"Formal AI value framework with quarterly ExCo reporting"),(5,"Continuous AI commercial attribution with A/B testing infrastructure and real-time revenue impact modelling")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of retail staff — including buyers, planners, store managers, and customer service — have received AI literacy training relevant to their role?",
             "options": [(1,"<5% — only e-commerce tech staff"),(2,"5–20% — mainly digital/data teams"),(3,"20–50% — digital and some commercial teams"),(4,"50–80% — broad coverage including buying, planning, and operations"),(5,">80% — universal coverage with role-specific AI modules for all functions including store teams")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI upskilling programme covering commercial AI tools — demand forecasting, personalisation, pricing, and customer insight analytics?",
             "options": [(1,"No programme — commercial teams discover AI tools themselves"),(2,"Generic digital skills courses only"),(3,"Structured programme for data/digital staff only"),(4,"Broad programme covering commercial, planning, and operations roles"),(5,"Comprehensive multi-tier programme with commercial AI simulation, vendor partnership training, and data literacy certification")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of commercial teams critically reviewing AI pricing and personalisation recommendations rather than accepting them unchallenged?",
             "options": [(1,"Very low — pricing AI outputs accepted without commercial review"),(2,"Informal — some buyers check AI recommendations"),(3,"Moderate — commercial review required for major pricing decisions"),(4,"High — formal commercial sign-off protocol for all AI pricing and ranging decisions"),(5,"Exemplary — structured human-AI commercial governance with override audit trail and AI training feedback loop")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have a Retail AI / Customer Intelligence Centre of Excellence driving personalisation and commercial AI standards?",
             "options": [(1,"No CoE — each category buys its own tools"),(2,"Informal community of practice with no mandate"),(3,"Small central data science team without CoE structure"),(4,"Established Commercial AI CoE with business engagement model and governance mandate"),(5,"Mature CoE with federated model — embedded AI analytics in every category and customer function")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage workforce change from AI-driven retail automation — store operations, fulfilment, and customer service AI?",
             "options": [(1,"No change management — automation deployed without colleague engagement"),(2,"Communication only — announce new system and move on"),(3,"Structured change management for major AI deployments"),(4,"Proactive reskilling aligned to automation roadmap with colleague involvement"),(5,"Comprehensive retail workforce transformation strategy with redeployment pathways and union/colleague forum engagement")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the organisation have a Responsible AI / Customer Trust Policy covering pricing fairness, personalisation transparency, and manipulation risk?",
             "options": [(1,"No AI ethics policy — general marketing policy applied"),(2,"Privacy policy updated to mention AI"),(3,"Draft responsible AI policy exists but is not formally adopted"),(4,"Formally adopted responsible AI policy with customer-facing commitments"),(5,"Comprehensive published AI customer trust charter with independent audit and annual transparency report")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a systematic process to detect and mitigate algorithmic bias — discriminatory pricing, unfair personalisation, or disparate customer outcomes based on demographics?",
             "options": [(1,"No bias testing for commercial AI"),(2,"Ad hoc review when customer complaints received"),(3,"Basic disparity analysis for highest-risk commercial AI"),(4,"Structured fairness assessment integrated into AI commercial deployment process"),(5,"Automated continuous fairness monitoring with disaggregated customer outcome reporting and public disclosure")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the AI regulatory compliance framework — covering GDPR consent for personalisation, DSA/DMA, Consumer Duty, and dark pattern prohibition?",
             "options": [(1,"No awareness of AI-specific retail regulations"),(2,"Aware of GDPR but no AI-specific compliance programme"),(3,"Compliance activities underway for highest-risk areas"),(4,"Comprehensive compliance programme covering GDPR, DSA, Consumer Duty, and dark pattern obligations"),(5,"Leading practice — proactive ICO/FCA engagement and ahead of all requirements")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Board / ExCo oversight with named accountability for AI customer risk — including reputational, pricing, and data risk?",
             "options": [(1,"No leadership visibility of AI customer risk"),(2,"AI risk mentioned generically in risk register"),(3,"ExCo receives periodic AI risk briefings"),(4,"Board/ExCo committee with explicit AI customer risk oversight mandate"),(5,"Dedicated board AI customer governance structure with CEO/CDAO joint accountability and external advisory board")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply privacy-by-design and customer consent architecture to all personalisation AI — including third-party data and cross-device tracking?",
             "options": [(1,"No AI-specific consent controls — general cookie banner applied"),(2,"Standard GDPR applied without personalisation AI-specific controls"),(3,"AI consent guidelines documented for personalisation"),(4,"Formal AI consent architecture with granular opt-in/out and data minimisation"),(5,"Privacy-by-design in all personalisation AI with ICO engagement and customer data rights portal")]},
        ],
    },

    # ── Education & Learning Services ──────────────────────────────────────
    "Education and learning services": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does institutional leadership have a formally endorsed AI in Education strategy — covering AI as a learning tool, academic integrity, and staff augmentation?",
             "options": [(1,"No AI in Education strategy"),(2,"Informal pilot discussions only"),(3,"Strategy draft in development with no senate/board endorsement"),(4,"Board/senate-endorsed AI strategy with learning outcome targets"),(5,"Comprehensive AI in Education strategy integrated into quality enhancement framework with external advisory input")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the institution's Academic Board or Quality Committee formally review AI's impact on learning quality, academic integrity, and equity?",
             "options": [(1,"Never — only if an academic integrity scandal occurs"),(2,"Annually in quality review cycle"),(3,"Quarterly Academic Board review"),(4,"Monthly quality committee with AI as standing agenda item"),(5,"Continuous real-time learning analytics reviewed regularly by academic leadership with student representation")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated AI in Education Lead or Chief Learning Technology Officer with authority over institutional AI adoption and academic integrity policy?",
             "options": [(1,"No dedicated role — AI driven by individual enthusiastic academics"),(2,"AI is an IT responsibility with no academic authority"),(3,"Named lead with limited budget and policy authority"),(4,"Dedicated AI in Education Director with policy mandate"),(5,"Chief Learning Technology Officer with board mandate, policy authority, and academic senate engagement")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate academic and administrative leadership AI literacy — including understanding AI's pedagogical potential, risks, and academic integrity implications?",
             "options": [(1,"Very low — leadership sees AI only as a threat to academic integrity"),(2,"Basic — aware of ChatGPT and plagiarism risks only"),(3,"Moderate — leadership understands learning analytics, adaptive learning, and integrity risks"),(4,"Strong — leadership actively drives AI pedagogy strategy"),(5,"Exemplary — leadership co-develops AI in Education research and practice with national bodies")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does senior leadership visibly champion AI as a tool to enhance learning and staff effectiveness — not merely to police academic dishonesty?",
             "options": [(1,"No positive leadership on AI — only restriction focus"),(2,"AI referenced in IT acceptable use policy only"),(3,"Occasional public commitment to positive AI use in learning"),(4,"Regular leadership communication on AI as a learning enhancement priority"),(5,"Vice-Chancellor/CEO-endorsed AI in Education charter with published commitments on equity, access, and learning outcomes")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are educational AI investments directly tied to measurable learning outcome KPIs — student attainment, retention, progression, and graduate employment?",
             "options": [(1,"No learning outcome KPIs defined for any AI project"),(2,"Vague 'improving student experience' without metrics"),(3,"KPIs defined for flagship projects only"),(4,"Most AI investments have tracked learning outcome business cases"),(5,"All AI investments governed by real-time learning analytics dashboards reviewed by Academic Board")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the EdTech AI portfolio governance across learning analytics, adaptive learning, AI tutors, and assessment tools?",
             "options": [(1,"No formal process — departments buy tools independently"),(2,"Informal prioritisation driven by vendor relationships"),(3,"Basic tracking with some senior leadership input"),(4,"Formal EdTech AI portfolio governance with pedagogical evidence and ethical review gates"),(5,"Mature portfolio management with student outcome evidence, equity impact assessment, and dynamic rebalancing")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do academic staff, learning technologists, and IT collaborate on AI tool design — ensuring AI enhances pedagogical goals?",
             "options": [(1,"Siloed — IT deploys tools, academics resist"),(2,"Academics consulted at UAT only"),(3,"Some joint design in curriculum development"),(4,"Co-design with academic champions embedded in AI tool development"),(5,"Fully integrated pedagogical-technology squads with shared student outcome accountability across faculties and IT")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the digital learning roadmap explicitly align AI investments to strategic education priorities — widening participation, skills for work, research excellence?",
             "options": [(1,"Technology roadmap built independently of education strategy"),(2,"Some AI tools referenced but not formally prioritised"),(3,"EdTech roadmap mapped to strategy but governed informally"),(4,"Digital learning roadmap co-developed with academic and student experience leadership"),(5,"Real-time strategy-technology alignment with AI as core to the institution's learning architecture")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal learning benefit realisation framework tracking AI's impact on student outcomes and staff efficiency?",
             "options": [(1,"No post-deployment tracking — tools purchased and forgotten"),(2,"Anecdotal staff feedback at year end"),(3,"Learning outcome review at 12 months for flagship tools only"),(4,"Formal benefits framework with annual academic board reporting"),(5,"Continuous learning analytics infrastructure with real-time AI impact attribution and equity disaggregation")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": True,
             "text": "What proportion of academic and professional services staff have received AI literacy training — covering responsible AI use, pedagogical application, and academic integrity?",
             "options": [(1,"<5% — only IT and learning technology staff"),(2,"5–20% — mainly digital learning specialists"),(3,"20–50% — learning technologists and some academic leads"),(4,"50–80% — broad academic and professional services coverage"),(5,">80% — universal coverage with role-specific AI pedagogy modules and CPD accreditation for all academic staff")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI upskilling programme covering both AI pedagogical skills and responsible AI use — including academic integrity, bias in AI feedback, and student data privacy?",
             "options": [(1,"No programme — staff discover AI tools themselves"),(2,"Generic online courses only"),(3,"Structured programme for learning technologists only"),(4,"Broad programme covering academic, library, and student support roles"),(5,"Comprehensive multi-tier programme with AI pedagogy design, academic integrity training, and PGCHE/CPD accreditation")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of academic staff critically evaluating AI learning tools — questioning algorithmic outputs and protecting professional pedagogical judgement?",
             "options": [(1,"Very low — academic staff accept AI feedback without critical engagement"),(2,"Informal — some academics question AI tools"),(3,"Moderate — academic freedom norm provides some critical check"),(4,"High — formal pedagogical review protocol for all AI learning recommendations"),(5,"Exemplary — structured academic AI ethics culture with faculty peer review of AI tools and student voice integration")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the institution have a Centre for Learning Technology or EdTech AI hub with mandate to govern AI tool standards and develop staff capability?",
             "options": [(1,"No hub — each department runs its own EdTech"),(2,"Informal learning technology community with no mandate"),(3,"Small central learning technology team without governance mandate"),(4,"Established Learning Technology Centre with EdTech AI governance and faculty engagement model"),(5,"Mature Learning Technology hub with federated model — embedded AI learning specialists in each faculty and school")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the institution manage the change from AI-enabled education — including student perception, equity of access, and staff wellbeing?",
             "options": [(1,"No change management — AI tools deployed without student or staff consultation"),(2,"Communication only — policy announcements without engagement"),(3,"Structured change management with staff and student consultation"),(4,"Proactive engagement with student union, academic senate, and staff unions"),(5,"Comprehensive AI education transition strategy with equity monitoring, student co-design, and staff wellbeing assessment")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": True,
             "text": "Does the institution have a formally adopted AI in Education Ethics Policy — covering algorithmic fairness, student data rights, privacy, and academic integrity?",
             "options": [(1,"No AI ethics policy — general AUP covers all technology"),(2,"Academic integrity policy updated to mention AI detectors"),(3,"AI ethics policy drafted but not formally adopted by board/senate"),(4,"Board-adopted AI in Education policy with student transparency commitments"),(5,"Comprehensive publicly committed AI ethics charter with student and staff rights, equity commitments, and annual external review")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a systematic process to detect and mitigate AI bias in assessment, learning analytics, and AI tutoring tools — particularly for underrepresented student groups?",
             "options": [(1,"No bias testing for educational AI"),(2,"Ad hoc review when student complaints received"),(3,"Basic disparity analysis for highest-risk assessment AI"),(4,"Structured fairness assessment for all AI tools with student demographic disaggregation"),(5,"Automated continuous equity monitoring with disaggregated student outcome reporting and public institutional equity report")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the regulatory compliance framework for educational AI — covering GDPR (student data), FERPA, UK GDPR, AI Act, and equality/accessibility legislation?",
             "options": [(1,"No awareness of AI-specific educational data regulations"),(2,"Aware of GDPR but no AI-specific compliance programme"),(3,"Compliance activities underway for highest-risk areas (student data)"),(4,"Comprehensive compliance programme covering GDPR, equality, accessibility, and AI Act"),(5,"Leading practice — proactive ICO engagement and accessibility review for all student-facing AI")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Board / Senate oversight with named accountability for AI ethics and student data risk in educational technology?",
             "options": [(1,"No leadership visibility of EdTech AI risk"),(2,"AI mentioned generically in information governance report"),(3,"Board receives periodic EdTech AI risk briefings"),(4,"Academic Board/Senate committee with explicit AI ethics oversight mandate"),(5,"Dedicated board AI ethics governance structure with student representative, academic freedom champion, and external ethics expert")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the institution apply data minimisation and informed student consent to all AI systems trained on student interaction, assessment, and engagement data?",
             "options": [(1,"No AI-specific student data controls — general data protection applied"),(2,"Standard GDPR applied without AI-specific student data safeguards"),(3,"AI data governance guidelines documented for learning analytics"),(4,"Formal AI student data governance with informed consent architecture"),(5,"Privacy-by-design in all EdTech AI with student data charter, transparency portal, and ICO engagement")]},
        ],
    },

    # ── Public Services & Citizen Support ───────────────────────────────────
    "Public services and citizen support": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does the public sector leadership have a formally endorsed AI strategy for citizen services — aligned to ministerial priorities, public value, and digital government objectives?",
             "options": [(1,"No AI strategy for public services"),(2,"Informal pilot discussions only"),(3,"Strategy draft in development with no minister/board endorsement"),(4,"Minister/board-endorsed AI strategy with citizen outcome targets"),(5,"Comprehensive AI strategy integrated into digital government framework with cross-departmental governance and HM Treasury approval")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the department's Executive Committee or Digital Board formally review AI public service quality, citizen impact, and accountability?",
             "options": [(1,"Never — only if a public scandal occurs"),(2,"Annually in departmental review"),(3,"Quarterly ExCo review with digital strategy"),(4,"Monthly digital board with AI as standing agenda item"),(5,"Continuous performance monitoring with weekly minister/board digital dashboard including citizen outcome metrics")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a Chief Digital Officer or AI Public Services Lead with real authority — including mandate over algorithmic decision-making in citizen-facing services?",
             "options": [(1,"No dedicated role — AI driven by individual programme managers"),(2,"AI is a shared IT responsibility with no citizen service authority"),(3,"Named lead with limited budget and policy authority"),(4,"CDO appointed with AI public services mandate"),(5,"Empowered CDO with minister-level accountability, algorithmic transparency remit, and cross-departmental governance authority")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate senior civil servant AI literacy — understanding algorithmic decision-making, fairness obligations, and public accountability requirements?",
             "options": [(1,"Very low — senior officials see AI as an IT project"),(2,"Basic awareness of AI chatbots and efficiency tools"),(3,"Moderate — officials understand algorithmic accountability and judicial review risk"),(4,"Strong — senior officials actively engage with AI ethics and public accountability"),(5,"Exemplary — officials drive responsible AI public services agenda nationally and internationally")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does ministerial/board leadership visibly champion AI public accountability, citizen rights, and digital inclusion as strategic priorities — not just efficiency?",
             "options": [(1,"No visible leadership on AI beyond cost-saving"),(2,"AI referenced in efficiency programmes only"),(3,"Occasional public commitment to responsible AI"),(4,"Regular ministerial/board communication on AI accountability and inclusion"),(5,"Minister/CEO-endorsed AI public services charter with citizen rights, accessibility, and accountability commitments published and independently audited")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are public service AI initiatives directly tied to citizen outcome KPIs — time-to-decision, accuracy rate, citizen satisfaction, and appeals/complaints rate?",
             "options": [(1,"No citizen outcome KPIs defined for any AI project"),(2,"Vague 'efficiency' goals without citizen impact measurement"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked citizen outcome business cases"),(5,"All AI investments governed by real-time citizen outcome dashboards with parliamentary/board accountability")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the algorithmic impact assessment (AIA) and spending review process for AI investments in public services?",
             "options": [(1,"No formal AIA or investment governance"),(2,"Basic cost-benefit analysis only — no citizen impact"),(3,"AIA required for highest-risk AI decisions only"),(4,"Formal AIA and HM Treasury business case required for all AI investments"),(5,"Leading AIA practice — proactive citizen and parliamentary engagement before deployment of all automated decisions")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do policy, operations, legal, and technology teams collaborate on AI public services design — with shared citizen outcome accountability?",
             "options": [(1,"Siloed — technology builds, policy objects after deployment"),(2,"Policy consulted at sign-off only"),(3,"Some joint design in service design phases"),(4,"Integrated policy-technology-legal squads with shared citizen outcome accountability"),(5,"Fully integrated multi-disciplinary AI public services squads with citizen co-design and democratic oversight")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the digital government roadmap explicitly prioritise AI investments aligned to public value objectives — inclusion, efficiency, accountability, and service access?",
             "options": [(1,"Technology roadmap built independently of policy priorities"),(2,"Some AI tools referenced but not formally prioritised"),(3,"Digital roadmap mapped to ministerial priorities but governed informally"),(4,"Digital roadmap co-developed with policy and citizen experience leadership"),(5,"Real-time strategy-technology alignment with AI governed under public value framework and parliamentary scrutiny")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal public value realisation framework tracking AI's citizen impact — including accessibility, unintended consequences, and marginalised group effects?",
             "options": [(1,"No post-deployment citizen impact tracking"),(2,"Anecdotal stakeholder feedback at project close"),(3,"Citizen satisfaction review at 12 months only"),(4,"Formal citizen impact framework with annual parliamentary/board reporting"),(5,"Continuous citizen outcome monitoring with disaggregated impact data and public transparency report")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of civil servants and public service staff have received AI literacy training — covering algorithmic accountability, bias, and citizen rights?",
             "options": [(1,"<5% — only digital specialists"),(2,"5–20% — mainly digital and data teams"),(3,"20–50% — digital and some policy and operational teams"),(4,"50–80% — broad coverage including front-line, policy, and legal teams"),(5,">80% — universal coverage with role-specific algorithmic accountability modules for all civil servants handling AI-assisted decisions")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured civil service AI upskilling programme covering responsible AI, algorithmic transparency, and citizen-centred design?",
             "options": [(1,"No programme — staff self-direct learning"),(2,"Generic digital skills courses only"),(3,"Structured programme for digital specialists only"),(4,"Broad programme covering policy, operations, legal, and digital roles"),(5,"Comprehensive multi-tier programme with algorithmic accountability modules, legal AI literacy, and GDS/CDDO accreditation for all AI-adjacent civil service roles")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of civil servants critically reviewing AI recommendations in citizen-facing decisions — and exercising meaningful human judgement?",
             "options": [(1,"Very low — AI decisions implemented without meaningful human review"),(2,"Informal norm to check AI output — no formal protocol"),(3,"Moderate — senior officer sign-off required for automated decisions only"),(4,"High — formal human-in-the-loop protocol for all citizen-affecting AI decisions"),(5,"Exemplary — structured civil servant accountability framework with meaningful review, override rights, and full audit trail for all AI-assisted decisions")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have a Digital / AI Centre of Excellence with mandate to govern algorithmic standards and develop civil servant capability?",
             "options": [(1,"No CoE — each department builds its own AI"),(2,"Informal digital community with no mandate"),(3,"Small central digital team without CoE structure"),(4,"Established Digital CoE with AI governance mandate and departmental engagement"),(5,"Mature AI CoE with federated model — embedded AI specialists in each department and arms-length body with cross-government standards authority")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage change from AI-driven public service transformation — including digital exclusion risk and staff displacement?",
             "options": [(1,"No change management — digital transformation deployed without citizen or staff engagement"),(2,"Communication only — press releases and policy papers"),(3,"Structured change management for major AI service transformations"),(4,"Proactive digital inclusion programme and staff reskilling aligned to AI roadmap"),(5,"Comprehensive public service transformation strategy with digital inclusion commitments, union agreement, and citizen co-design embedded in every AI deployment")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": True,
             "text": "Does the organisation have a formally adopted Algorithmic Transparency and AI Ethics Policy — covering automated decision-making, citizen rights, and appeal mechanisms?",
             "options": [(1,"No AI ethics policy — general public sector values apply"),(2,"Generic digital ethics principles referenced without specific AI obligations"),(3,"AI ethics policy drafted but not formally adopted"),(4,"Formally adopted algorithmic transparency policy with citizen notice and appeal rights"),(5,"Comprehensive published algorithmic register with citizen rights, independent audit, and parliamentary scrutiny protocol")]},
            {"id": "p4_q2", "weight": 1.4, "critical": True,
             "text": "Is there a systematic process for detecting and mitigating algorithmic bias in citizen-facing automated decisions — particularly for protected characteristics and marginalised groups?",
             "options": [(1,"No bias testing for public service AI"),(2,"Ad hoc review when public complaints received"),(3,"Basic disparity analysis for highest-risk automated decisions"),(4,"Structured fairness assessment for all citizen-facing AI with demographic disaggregation"),(5,"Automated continuous bias monitoring with real-time equity dashboards, public transparency report, and Equality and Human Rights Commission engagement")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the regulatory compliance framework — covering UK GDPR, Equality Act, Human Rights Act, EU AI Act, and administrative law obligations for automated decisions?",
             "options": [(1,"No awareness of AI-specific legal obligations in public services"),(2,"Aware of GDPR but no AI-specific compliance programme"),(3,"Compliance activities underway for highest-risk automated decisions"),(4,"Comprehensive compliance programme covering GDPR, equality, HRA, and EU AI Act"),(5,"Leading practice — proactive engagement with ICO, EHRC, and parliamentary committees; legal review embedded in all AI deployment approvals")]},
            {"id": "p4_q4", "weight": 1.2, "critical": True,
             "text": "Is there Board / Permanent Secretary oversight with named departmental accountability for algorithmic decision-making risk and citizen harm?",
             "options": [(1,"No leadership visibility of algorithmic risk"),(2,"AI mentioned in risk register only"),(3,"Board receives periodic AI risk briefings"),(4,"Board/Perm Sec with explicit algorithmic accountability mandate"),(5,"Dedicated board AI public accountability governance structure with citizen advisory panel, legal AI risk function, and parliamentary accountability mechanism")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply data minimisation and citizen consent principles to all AI systems using citizen data — including joined-up data sharing across public bodies?",
             "options": [(1,"No AI-specific citizen data controls — general data protection applied"),(2,"Standard UK GDPR applied without AI-specific safeguards"),(3,"AI data governance guidelines documented for citizen data"),(4,"Formal AI citizen data governance with minimisation, purpose limitation, and consent architecture"),(5,"Privacy-by-design in all public service AI with ICO engagement, data sharing agreements with democratic oversight, and citizen data transparency portal")]},
        ],
    },

    # ── Telecommunications ───────────────────────────────────────────────────
    "Telecommunications": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does telecoms leadership have a formally documented AI strategy covering network AI, customer experience, and predictive operations — endorsed at Group ExCo level?",
             "options": [(1,"No AI strategy"),(2,"Informal AI pilot discussions only"),(3,"Strategy draft with no ExCo endorsement"),(4,"ExCo-endorsed AI strategy with network and CX KPI targets"),(5,"Comprehensive AI strategy integrated into network evolution and commercial plan with 5G/6G alignment")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does telecoms leadership review AI transformation progress against network SLA, ARPU, and customer experience KPIs?",
             "options": [(1,"Never — only if a major network or NPS incident occurs"),(2,"Annually in the network strategy review"),(3,"Quarterly ExCo review"),(4,"Monthly ExCo with AI KPIs as standing agenda item"),(5,"Continuous real-time network AI dashboards with weekly ExCo review and board-level reporting")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Chief Network AI / Data Officer with authority over AIOps, predictive network management, and AI customer experience investments?",
             "options": [(1,"No dedicated role"),(2,"AI shared between network engineering and IT"),(3,"Named lead with limited authority"),(4,"Dedicated AI/Data Officer with network and CX mandate"),(5,"Group CDAO with board access, AIOps strategy authority, and regulatory engagement remit")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate telecoms leadership AI literacy — covering AIOps, predictive maintenance, network slicing AI, and AI-driven churn management?",
             "options": [(1,"Very low — leadership sees AI as a technology topic only"),(2,"Basic awareness — understands AI chatbots and fraud detection"),(3,"Moderate — leadership understands AIOps, predictive maintenance, and AI churn management"),(4,"Strong — leadership actively drives AI network and commercial strategy"),(5,"Exemplary — leadership benchmarks AI against global telco leaders and contributes to GSMA/ITU AI standards")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does telecoms leadership visibly champion AI as a network quality, customer trust, and sustainability priority — beyond cost reduction?",
             "options": [(1,"No visible leadership on AI beyond capex reduction"),(2,"AI referenced in annual report only"),(3,"Occasional commitment to AI-driven network quality"),(4,"Regular leadership communication on AI as a quality and sustainability priority"),(5,"CEO-endorsed AI network excellence programme with published NPS, SLA, and carbon reduction targets tied to AI initiatives")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are telecoms AI investments directly tied to measurable KPIs — network uptime, MTTR, NPS, ARPU, churn rate, and opex reduction per site?",
             "options": [(1,"No operational KPIs defined for any AI project"),(2,"Vague efficiency goals without measurement"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked operational and commercial business cases"),(5,"All AI investments governed by real-time network and commercial dashboards with ExCo KPI review")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the AI portfolio governance across network AI (AIOps, predictive), customer AI (personalisation, churn), and operational AI (field force, procurement)?",
             "options": [(1,"No formal process — network and IT approve independently"),(2,"Informal prioritisation within technology function"),(3,"Basic portfolio tracking with some ExCo input"),(4,"Formal AI portfolio governance with business case and KPI gates"),(5,"Mature portfolio management with ROI tracking, technology readiness, and dynamic rebalancing across network and commercial functions")]},
            {"id": "p2_q3", "weight": 1.3, "critical": True,
             "text": "How effectively do network engineering, IT, commercial, and customer operations collaborate on AI solutions — with shared SLA and NPS accountability?",
             "options": [(1,"Completely siloed — network and commercial never share AI accountability"),(2,"Limited collaboration at product launch boundaries"),(3,"Some joint squads for major AI programmes"),(4,"Integrated network-commercial-IT teams with shared uptime and NPS accountability"),(5,"Fully integrated cross-functional AI squads with joint SLA, NPS, and opex accountability across network and commercial domains")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the network technology roadmap explicitly prioritise AI use cases aligned to commercial strategy — 5G monetisation, enterprise growth, fibre rollout efficiency?",
             "options": [(1,"Network roadmap built independently of commercial strategy"),(2,"Some AI tools referenced but not formally prioritised"),(3,"Network AI roadmap mapped to commercial priorities but governed informally"),(4,"Network and commercial roadmap co-developed with joint AI investment prioritisation"),(5,"Real-time network-commercial strategy alignment with AI as the core intelligent network platform")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal ROI framework tracking AI value in network operations, field force, and customer experience — with attribution modelling?",
             "options": [(1,"No post-deployment value tracking"),(2,"Anecdotal cost saving at project close"),(3,"Opex tracking at 12 months for flagship tools only"),(4,"Formal AI value framework with quarterly ExCo reporting"),(5,"Continuous AI value attribution with automated opex reconciliation and commercial impact modelling")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of network engineers, field technicians, and customer operations staff have received AI literacy training relevant to their role?",
             "options": [(1,"<5% — only data/IT specialists"),(2,"5–20% — mainly data scientists and AI platform teams"),(3,"20–50% — technical and some customer operations teams"),(4,"50–80% — broad coverage including field force and customer service"),(5,">80% — universal coverage with role-specific AIOps and customer AI modules for all technical and commercial staff")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI upskilling programme covering AIOps tools, AI-assisted field operations, and AI customer engagement for telecoms employees?",
             "options": [(1,"No programme — staff discover AI tools themselves"),(2,"Generic online courses only"),(3,"Structured programme for network AI specialists only"),(4,"Broad programme covering network, field force, and customer operations roles"),(5,"Comprehensive multi-tier programme with AIOps certification, field AI simulation, and customer AI specialist qualification")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of network operations and field teams critically reviewing AI-generated alerts and recommendations — rather than blindly executing?",
             "options": [(1,"Very low — AIOps alerts executed without engineering review"),(2,"Informal — some engineers check, many do not"),(3,"Moderate — senior engineer sign-off for high-impact AIOps actions"),(4,"High — formal human validation protocol for all AI-triggered network interventions"),(5,"Exemplary — structured NOC human-AI teaming framework with override audit trail and AI alert quality feedback loop")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have a Network AI / Data Science Centre of Excellence driving AIOps standards and building intelligent network capability?",
             "options": [(1,"No CoE — each network domain builds its own AI"),(2,"Informal data science community with no mandate"),(3,"Small central data science team without CoE structure"),(4,"Established Network AI CoE with AIOps standards and domain engagement model"),(5,"Mature CoE with federated model — embedded AI engineers in radio, core, transport, and commercial domains")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the telecoms organisation manage workforce change from AIOps and network automation — including field force role redesign and reskilling?",
             "options": [(1,"No change management — automation deployed without workforce planning"),(2,"Communication only"),(3,"Structured change management for major automation deployments"),(4,"Proactive reskilling aligned to automation roadmap with union engagement"),(5,"Comprehensive workforce transformation strategy with field force redeployment pathways, union agreement, and employee involvement in automation design")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the telecoms organisation have a Responsible AI Policy covering network AI fairness, customer data use, and algorithmic transparency in customer-facing systems?",
             "options": [(1,"No AI ethics policy — general corporate values applied"),(2,"Privacy policy updated to mention AI"),(3,"Draft responsible AI policy exists but not formally adopted"),(4,"Formally adopted responsible AI policy with customer transparency commitments"),(5,"Comprehensive published AI ethics charter with independent review, annual transparency report, and GSMA Responsible AI commitment")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a systematic process for detecting and mitigating algorithmic bias in customer-facing AI — pricing, service quality allocation, and churn management?",
             "options": [(1,"No bias testing for customer AI"),(2,"Ad hoc review when regulatory complaint received"),(3,"Basic disparity analysis for highest-risk customer AI"),(4,"Structured fairness assessment for all customer-facing AI"),(5,"Automated continuous bias monitoring with disaggregated customer outcome reporting and Ofcom engagement")]},
            {"id": "p4_q3", "weight": 1.3, "critical": True,
             "text": "How mature is the telecoms AI regulatory compliance framework — covering EU AI Act, UK GDPR, NIS2, Ofcom/FCC sector rules, and network resilience obligations?",
             "options": [(1,"No awareness of AI-specific telecoms regulations"),(2,"Aware of GDPR and Ofcom rules but no AI-specific programme"),(3,"Compliance for most critical regulations underway"),(4,"Comprehensive programme covering GDPR, NIS2, EU AI Act, and Ofcom requirements"),(5,"Leading practice — proactive Ofcom and regulatory engagement, ahead of all AI compliance requirements")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Board / ExCo oversight with named accountability for AI risk in network operations and customer-facing systems?",
             "options": [(1,"No leadership visibility of AI risk"),(2,"AI mentioned generically in risk register"),(3,"ExCo receives periodic AI risk briefings"),(4,"ExCo/Board with explicit AI risk oversight mandate"),(5,"Dedicated board AI governance structure with CISO/CDAO joint accountability and external advisory panel")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply data minimisation and customer consent principles to all AI models trained on network usage and customer behavioural data?",
             "options": [(1,"No AI-specific customer data controls"),(2,"Standard GDPR applied without AI-specific controls"),(3,"AI data governance guidelines documented"),(4,"Formal AI consent architecture with granular opt-in/out and data minimisation"),(5,"Privacy-by-design in all AI with ICO engagement, customer data transparency portal, and real-time consent management")]},
        ],
    },

    # ── Logistics & Transport ──────────────────────────────────────────────
    "Logistics and transport": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does logistics/transport leadership have a formally endorsed AI strategy — covering route optimisation, demand forecasting, fleet AI, and last-mile delivery?",
             "options": [(1,"No AI strategy"),(2,"Informal AI pilot discussions only"),(3,"Strategy draft not board-endorsed"),(4,"Board-endorsed AI strategy with operational KPI targets"),(5,"Comprehensive AI strategy integrated into network design, fleet investment, and customer SLA commitments")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does logistics/transport leadership formally review AI transformation progress against on-time delivery, cost-per-shipment, and fleet utilisation KPIs?",
             "options": [(1,"Never — only when a delivery failure occurs"),(2,"Annually in operational review"),(3,"Quarterly board review"),(4,"Monthly operational board with AI KPIs as standing item"),(5,"Continuous real-time AI operations dashboards with weekly leadership review and customer SLA tracking")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Head of AI/Digital Operations with authority over route optimisation AI, predictive fleet management, and warehouse automation investments?",
             "options": [(1,"No dedicated role — AI driven by operations managers"),(2,"AI is a shared IT responsibility"),(3,"Named lead with limited authority"),(4,"Head of Digital Operations with AI mandate"),(5,"CDO/COO joint role with board authority, AI investment mandate, and sustainability AI remit")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate logistics leadership AI literacy — covering route optimisation algorithms, demand sensing AI, predictive maintenance, and AI-driven warehouse operations?",
             "options": [(1,"Very low — leadership sees AI as an IT topic"),(2,"Basic — aware of basic route planning tools only"),(3,"Moderate — leadership understands optimisation, demand sensing, and predictive maintenance AI"),(4,"Strong — leadership actively drives AI operations strategy"),(5,"Exemplary — leadership benchmarks AI against global logistics leaders and participates in industry AI consortia")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does senior leadership visibly champion AI as an operational excellence, sustainability, and driver/colleague welfare priority — not just a cost reduction tool?",
             "options": [(1,"No visible leadership on AI beyond cost-cutting"),(2,"AI referenced in efficiency programmes only"),(3,"Occasional commitment to AI-driven efficiency"),(4,"Regular leadership communication on AI as an operational and sustainability priority"),(5,"CEO-endorsed AI operations excellence programme with published on-time, carbon, and driver welfare KPIs tied to AI initiatives")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": True,
             "text": "Are logistics/transport AI investments directly tied to measurable operational KPIs — on-time delivery, cost-per-shipment, fleet utilisation, and carbon emissions per km?",
             "options": [(1,"No operational KPIs defined for any AI project"),(2,"Vague efficiency goals without measurement"),(3,"KPIs defined for flagship projects only"),(4,"Most AI projects have tracked operational business cases"),(5,"All AI investments governed by real-time operational dashboards with ExCo and customer SLA review")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the AI portfolio governance across route optimisation, predictive maintenance, warehouse robotics, demand forecasting, and last-mile AI?",
             "options": [(1,"No formal process — operations approve tools independently"),(2,"Informal prioritisation by operations managers"),(3,"Basic tracking with some leadership input"),(4,"Formal AI portfolio governance with operational business case gates"),(5,"Mature portfolio management with ROI tracking and dynamic rebalancing across all logistics AI domains")]},
            {"id": "p2_q3", "weight": 1.3, "critical": True,
             "text": "How effectively do dispatch operations, warehouse, fleet management, and technology teams collaborate on AI solutions — with shared delivery and cost accountability?",
             "options": [(1,"Siloed — technology deploys, operations rejects"),(2,"Limited collaboration at system handoff only"),(3,"Some joint working in warehouse and dispatch AI"),(4,"Integrated operations-technology teams with shared delivery KPI accountability"),(5,"Fully integrated AI squads with co-ownership of on-time, cost-per-shipment, and carbon metrics across all operations functions")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the logistics technology roadmap explicitly prioritise AI use cases aligned to commercial strategy — new market entry, same-day capability, sustainability?",
             "options": [(1,"Technology roadmap built independently of commercial strategy"),(2,"Some AI tools referenced but not prioritised"),(3,"AI roadmap mapped to commercial strategy but governed informally"),(4,"Technology roadmap co-developed with commercial and operations leadership"),(5,"Real-time strategy-technology alignment with AI as the core intelligent operations platform")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal ROI and sustainability impact framework tracking AI value in logistics operations — including carbon reduction attribution?",
             "options": [(1,"No post-deployment value tracking"),(2,"Anecdotal cost saving at project close"),(3,"Operational cost tracking at 12 months only"),(4,"Formal AI value framework with quarterly leadership reporting"),(5,"Continuous AI value attribution with automated cost, delivery, and carbon impact reconciliation")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of operations staff — drivers, warehouse operatives, dispatchers, and planners — have received AI literacy training relevant to their role?",
             "options": [(1,"<5% — only data/IT specialists"),(2,"5–20% — planners and some supervisors"),(3,"20–50% — planners, supervisors, and warehouse team leaders"),(4,"50–80% — broad coverage including drivers and operatives"),(5,">80% — universal coverage with role-specific AI modules for all operations roles including drivers and warehouse operatives")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI upskilling programme covering route optimisation tools, warehouse robotics co-working, and AI dispatch systems for operations employees?",
             "options": [(1,"No programme — operatives discover AI tools themselves"),(2,"Generic digital skills courses only"),(3,"Structured programme for planners and supervisors only"),(4,"Broad programme covering operations, warehouse, and driver roles"),(5,"Comprehensive multi-tier programme with hands-on robotics training, AI dispatch simulation, and transport industry qualifications")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of dispatchers and operations teams critically reviewing AI route and load recommendations before actioning — particularly in edge cases?",
             "options": [(1,"Very low — AI recommendations executed without operational review"),(2,"Informal — some planners check, most do not"),(3,"Moderate — senior dispatcher review for unusual AI recommendations"),(4,"High — formal operational sign-off protocol for all AI route and dispatch decisions"),(5,"Exemplary — structured human-AI dispatch governance with override audit trail and feedback loop into AI model retraining")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have an Operations AI Centre of Excellence driving route optimisation, predictive maintenance, and warehouse AI standards?",
             "options": [(1,"No CoE — each depot buys its own tools"),(2,"Informal operations community with no mandate"),(3,"Small central operations technology team without CoE structure"),(4,"Established Operations AI CoE with standards and depot engagement model"),(5,"Mature CoE with federated model — embedded AI specialists in each distribution centre and transport hub")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage workforce change from AI-driven logistics automation — including driver role evolution, warehouse robotics, and gig economy AI tools?",
             "options": [(1,"No change management — automation deployed without workforce planning"),(2,"Communication only"),(3,"Structured change management for major automation deployments"),(4,"Proactive reskilling aligned to automation roadmap with union engagement"),(5,"Comprehensive workforce transformation strategy with redeployment pathways, union agreement, and driver/operative co-design of AI tools")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the organisation have a Responsible AI and Safety Policy covering AI in fleet management, warehouse robotics safety, and autonomous vehicle governance?",
             "options": [(1,"No AI safety policy — general H&S applied"),(2,"General machinery safety policy referenced for AI systems"),(3,"Draft AI safety policy not formally adopted"),(4,"Formally adopted AI operations safety policy with fleet and warehouse AI requirements"),(5,"Comprehensive AI safety governance with functional safety assessment, autonomous vehicle governance, and transport regulatory compliance framework")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a systematic process for validating AI route and load recommendations before they are actioned — to prevent delivery failures, accidents, or regulatory breaches?",
             "options": [(1,"No validation — AI outputs actioned automatically"),(2,"Ad hoc review when an incident occurs"),(3,"Validation for highest-risk AI decisions only"),(4,"Structured operational sign-off before AI-generated routes actioned in edge cases"),(5,"Formal safety case for autonomous and high-risk AI decisions with DVSA/IRU regulatory compliance review")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the logistics AI regulatory compliance framework — covering EU AI Act, tachograph AI, GDPR (driver data), HGV driver monitoring, and autonomous vehicle regulation?",
             "options": [(1,"No awareness of AI-specific logistics regulations"),(2,"Aware of GDPR and HGV rules but no AI-specific programme"),(3,"Compliance for most critical areas underway"),(4,"Comprehensive compliance programme covering GDPR, tachograph AI, and transport regulations"),(5,"Leading practice — proactive DVSA/EU regulatory engagement and ahead of autonomous vehicle AI requirements")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Board / ExCo oversight with named accountability for AI safety and operational risk in logistics — including third-party AI gig platform risk?",
             "options": [(1,"No board visibility of AI operational risk"),(2,"AI mentioned generically in risk register"),(3,"ExCo receives periodic AI risk briefings"),(4,"Board/ExCo with explicit AI operational risk oversight mandate"),(5,"Dedicated board AI safety governance with COO/CISO joint accountability and supply chain AI risk audit programme")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply data minimisation and driver consent principles to all AI systems using driver telematics, location, and behavioural monitoring data?",
             "options": [(1,"No AI-specific driver data controls"),(2,"Standard GDPR applied without AI-specific controls"),(3,"AI driver data governance documented"),(4,"Formal AI consent architecture with driver transparency statement and minimisation controls"),(5,"Privacy-by-design in all driver AI with ICO engagement, driver data portal, and union-agreed monitoring protocol")]},
        ],
    },

    # ── Agriculture & Rural Services ─────────────────────────────────────────
    "Agriculture and rural services": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Do agricultural business or cooperative leadership have a formally documented Precision Agriculture / AgriTech AI strategy endorsed at a board or membership level?",
             "options": [(1,"No AI or precision agriculture strategy"),(2,"Informal discussions about a few technology tools"),(3,"Strategy draft in development without formal adoption"),(4,"Board/membership-endorsed AI strategy with yield and sustainability targets"),(5,"Comprehensive precision agriculture strategy integrated into farm business plan and subsidy/grant applications")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does farm or cooperative leadership formally review AI and precision agriculture technology progress against yield, cost, and sustainability KPIs?",
             "options": [(1,"Never — technology decisions are reactive"),(2,"Annually at AGM"),(3,"Seasonally (twice a year) at harvest and planning reviews"),(4,"Quarterly with farm management committee"),(5,"Continuous real-time farm management dashboards reviewed monthly with agronomists and cooperative leadership")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Farm Digital Lead / AgriTech Advisor with real authority to guide AI adoption and precision agriculture investments across the operation?",
             "options": [(1,"No dedicated lead — technology left to individual farmer preference"),(2,"AI guided by equipment dealers only"),(3,"Part-time advisor with limited authority and budget"),(4,"Dedicated AgriTech lead with advisory mandate and procurement authority"),(5,"Farm/cooperative CDO or AgriTech Director with board mandate, grant management, and ecosystem partnership authority")]},
            {"id": "p1_q4", "weight": 1.0, "critical": True,
             "text": "How would you rate farm and cooperative leadership digital and AI literacy — including understanding of precision agriculture data, crop modelling AI, and agri-data privacy?",
             "options": [(1,"Very low — AI seen as irrelevant or threatening to traditional practice"),(2,"Basic — aware of GPS tractors and basic sensors"),(3,"Moderate — leadership understands variable rate application, weather AI, and NDVI imaging"),(4,"Strong — leadership actively drives precision agriculture decisions using AI insights"),(5,"Exemplary — leadership participates in agri-data consortia, co-develops AI with research institutes, and contributes to policy")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does leadership visibly champion AI and precision agriculture as a sustainability, food security, and farm profitability priority — not just a technology experiment?",
             "options": [(1,"No visible leadership commitment to AI/precision agriculture"),(2,"AI referenced in grant applications only"),(3,"Occasional public commitment to sustainable farming technology"),(4,"Regular leadership communication on precision agriculture as a strategic priority"),(5,"CEO/Chair-endorsed AI farming strategy with published yield, water, carbon, and biodiversity targets tied to precision agriculture investment")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are agricultural AI investments directly tied to measurable farm KPIs — yield per hectare, input cost reduction, water use efficiency, carbon footprint, and quality grade improvement?",
             "options": [(1,"No farm KPIs defined for any AI investment"),(2,"Vague productivity goals without measurement"),(3,"KPIs defined for a few precision tools only"),(4,"Most AI investments have tracked farm business case KPIs"),(5,"All AI investments governed by real-time farm management dashboards with agronomist and cooperative review")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the precision agriculture technology governance across crop modelling, variable rate application, livestock AI, and supply chain traceability?",
             "options": [(1,"No formal process — technology selected by individual farmers or dealers"),(2,"Informal decisions based on equipment manufacturer recommendations"),(3,"Basic evaluation with some agronomist input"),(4,"Formal AgriTech portfolio governance with farm business case and agronomist review"),(5,"Mature portfolio management with ROI tracking, agronomic evidence review, and grant optimisation strategy")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do farmers, agronomists, cooperatives, and technology providers collaborate on AI tool design — ensuring tools work in real farm conditions?",
             "options": [(1,"No collaboration — farmers receive technology from dealers"),(2,"Farmers consulted at trial stage only"),(3,"Some joint trialling on-farm with agronomist involvement"),(4,"Co-design with farmers and agronomists embedded in AgriTech development"),(5,"Fully integrated farmer-agronomist-technology co-design with real-world farm validation and cooperative governance of AI tools")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the farm technology roadmap explicitly align AI investments to commercial strategy — premium market access, food safety certification, export standards, sustainability premiums?",
             "options": [(1,"Technology choices made independently of commercial strategy"),(2,"Some tools referenced in farm business plan"),(3,"AgriTech roadmap loosely mapped to commercial priorities"),(4,"Technology roadmap co-developed with commercial partners and cooperative leadership"),(5,"Real-time farm-commercial strategy alignment with AI as the core precision agriculture platform and traceability system")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal ROI and sustainability benefits framework tracking AI value in farm operations — including yield improvement, input cost, and carbon credit generation?",
             "options": [(1,"No post-deployment value tracking — technology purchased and forgotten"),(2,"Anecdotal yield improvement reported to cooperative annually"),(3,"Yield and cost review at end of season only"),(4,"Formal farm AI value framework with seasonal agronomist reporting"),(5,"Continuous farm AI value attribution with real-time yield, cost, carbon, and biodiversity monitoring integrated with cooperative reporting and subsidy management")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": True,
             "text": "What proportion of farm workers, cooperative members, and rural service staff have received foundational AgriTech and AI literacy training relevant to their work?",
             "options": [(1,"<5% — only technical specialists in large operations"),(2,"5–20% — mainly cooperative technical advisors"),(3,"20–50% — technical advisors and progressive farm managers"),(4,"50–80% — broad coverage including farm workers and smallholder cooperative members"),(5,">80% — near-universal coverage with locally accessible AgriTech training in appropriate languages and formats")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AgriTech upskilling programme covering precision agriculture tools, crop modelling AI, livestock monitoring, and agri-data management — designed for rural contexts?",
             "options": [(1,"No programme — farmers left entirely to vendor training"),(2,"Generic digital literacy courses — not agriculture-specific"),(3,"Structured programme for cooperative technical advisors only"),(4,"Broad programme covering farmers, cooperative members, and rural service workers"),(5,"Comprehensive locally-delivered programme with hands-on farm trials, offline capability, and accredited AgriTech qualifications recognisable in rural communities")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of farmers critically evaluating AI crop and livestock recommendations alongside their own agronomic experience and local knowledge?",
             "options": [(1,"Very low — AI recommendations followed without local knowledge validation"),(2,"Informal — some experienced farmers question AI advice"),(3,"Moderate — agronomist review encouraged for AI recommendations on high-value crops"),(4,"High — formal farmer-agronomist review protocol for all AI-driven treatment and input decisions"),(5,"Exemplary — structured human-AI agronomy framework combining AI insights with traditional ecological knowledge and independent agronomist validation")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation / cooperative have an AgriTech knowledge hub or innovation centre driving precision agriculture standards and building farmer capability?",
             "options": [(1,"No hub — farmers access technology individually through dealers"),(2,"Informal knowledge sharing at cooperative meetings only"),(3,"Small cooperative technical team without innovation mandate"),(4,"Established AgriTech hub with precision agriculture governance and member engagement model"),(5,"Mature innovation centre with federated model — embedded AgriTech advisors serving each farming cluster and rural community with accessible in-field support")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage change from AgriTech adoption — including digital access barriers, generational differences, and smallholder inclusion?",
             "options": [(1,"No change management — technology deployed without farmer engagement"),(2,"Information leaflets only"),(3,"Structured outreach for major AgriTech deployments"),(4,"Proactive inclusion programme addressing digital access and generational barriers"),(5,"Comprehensive rural digital inclusion strategy with offline fallback, intergenerational knowledge sharing, and smallholder-specific support ensuring no farmer is left behind")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the organisation / cooperative have a formal Responsible AgriTech Policy covering data privacy for farmers, algorithmic fairness in subsidy AI, and environmental ethics?",
             "options": [(1,"No policy — general IT terms of service accepted"),(2,"Vendor privacy policy referenced as sufficient"),(3,"Draft responsible AgriTech policy not formally adopted"),(4,"Adopted responsible AgriTech policy with farmer data rights and subsidy AI fairness commitments"),(5,"Comprehensive published AgriTech ethics charter with farmer data sovereignty, environmental impact assessment, and independent agri-data audit")]},
            {"id": "p4_q2", "weight": 1.4, "critical": False,
             "text": "Is there a systematic process for identifying and mitigating AI bias in precision agriculture recommendations — particularly disparate impacts on smallholders vs. large commercial farms?",
             "options": [(1,"No bias consideration for AgriTech AI"),(2,"Ad hoc review when farmer complaints received"),(3,"Basic fairness consideration for subsidy allocation AI only"),(4,"Structured fairness assessment for all AI tools with smallholder and equity impact analysis"),(5,"Automated equity monitoring of AgriTech AI with disaggregated impact reporting by farm size, geography, and demographic with public transparency report")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the regulatory compliance framework for agricultural AI — covering GDPR (farm data), EU AI Act, agri-data governance codes, and rural subsidy algorithm transparency?",
             "options": [(1,"No awareness of AI-specific agricultural regulations"),(2,"Aware of GDPR but no agricultural AI-specific programme"),(3,"Compliance for most critical regulations underway"),(4,"Comprehensive compliance programme covering GDPR, EU AI Act, and agri-data governance codes"),(5,"Leading practice — proactive engagement with DEFRA/EC, ahead of agri-data governance requirements, and contributor to sector AI standards")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there cooperative board or farm business oversight with named accountability for AgriTech AI risk — including supplier data risk and subsidy algorithmic fairness?",
             "options": [(1,"No cooperative leadership visibility of AgriTech AI risk"),(2,"Technology risk mentioned generically in cooperative AGM"),(3,"Board receives periodic AgriTech risk briefings"),(4,"Cooperative board with explicit AgriTech AI risk oversight mandate"),(5,"Dedicated cooperative AI governance structure with farmer representative, agronomist expert, and regulatory body engagement")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply farm data sovereignty and minimal data sharing principles to all AI systems using precision agriculture, livestock, and farm business data?",
             "options": [(1,"No farmer data controls — vendor terms accepted"),(2,"Standard GDPR applied without farm-specific data controls"),(3,"Agri-data governance guidelines documented for key platforms"),(4,"Formal farm data sovereignty framework with data minimisation and portable data rights"),(5,"Privacy-by-design in all AgriTech AI with farmer data trust model, cooperative data governance, and interoperability standards ensuring farmer data portability")]},
        ],
    },

    # ── Human Resources & Shared Services ─────────────────────────────────
    "Human resources and shared services": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does HR leadership have a formally documented People Analytics / AI in HR strategy — covering AI-assisted hiring, performance, L&D, and workforce planning?",
             "options": [(1,"No AI in HR strategy"),(2,"Informal discussions about automating recruitment only"),(3,"Strategy draft not CHRO/board-endorsed"),(4,"CHRO/board-endorsed AI in HR strategy with fairness and efficiency targets"),(5,"Comprehensive People Analytics strategy integrated into workforce plan with employee rights, fairness commitments, and legal review")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the CHRO or People Committee formally review AI-driven HR decisions — hiring outcomes, performance scores, pay equity — for fairness and accuracy?",
             "options": [(1,"Never — HR AI decisions reviewed only when complaints arise"),(2,"Annually in HR audit cycle"),(3,"Quarterly People Committee review"),(4,"Monthly CHRO review with AI fairness metrics as standing agenda item"),(5,"Continuous real-time fairness dashboards reviewed regularly by CHRO, legal, and DEI teams with employee representative input")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated Head of People Analytics / AI in HR with authority over AI tool selection, algorithmic fairness governance, and HR data ethics?",
             "options": [(1,"No dedicated role — AI decided by individual HR business partners"),(2,"AI is a shared IT responsibility with no HR authority"),(3,"Named lead with limited budget and ethics authority"),(4,"Head of People Analytics with AI fairness mandate"),(5,"Chief People Analytics Officer with CHRO joint accountability, legal remit, and works council engagement authority")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate HR and executive leadership AI literacy — covering algorithmic bias in hiring, AI performance management risks, and employment law implications?",
             "options": [(1,"Very low — HR leaders accept vendor AI claims uncritically"),(2,"Basic — aware that AI can be biased but don't know how"),(3,"Moderate — HR leadership understands key bias types and legal exposure"),(4,"Strong — HR leadership actively governs AI fairness and legal compliance"),(5,"Exemplary — HR leadership co-develops AI ethics standards and engages with EHRC/ICO on responsible people analytics")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does leadership visibly champion AI in HR as an employee trust, fairness, and inclusion priority — not just a hiring efficiency tool?",
             "options": [(1,"No visible leadership commitment beyond automation ROI"),(2,"AI referenced in HR efficiency targets only"),(3,"Occasional public commitment to fair AI in HR"),(4,"Regular CHRO communication on AI fairness as a people strategy priority"),(5,"CEO/CHRO-endorsed AI in People charter with published commitments on fairness, transparency, employee rights, and independent audit")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are HR AI investments directly tied to measurable people outcome KPIs — time-to-hire, quality-of-hire, engagement score, retention, and L&D completion — not just cost reduction?",
             "options": [(1,"No people outcome KPIs — AI justified on cost only"),(2,"Vague 'productivity improvement' without employee outcome metrics"),(3,"KPIs defined for flagship projects only"),(4,"Most HR AI investments have tracked people outcome business cases"),(5,"All HR AI investments governed by real-time people dashboards with CHRO, DEI, and legal review alongside ROI tracking")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the AI portfolio governance across HR AI — covering ATS AI, performance management algorithms, pay equity analytics, and L&D personalisation?",
             "options": [(1,"No formal process — HR tools selected by individual HR business partners"),(2,"Informal prioritisation driven by vendor relationships"),(3,"Basic tracking with some CHRO input"),(4,"Formal HR AI portfolio governance with fairness review and legal sign-off gates"),(5,"Mature HR AI portfolio management with fairness audit, legal review, and employee representative consultation at each governance stage")]},
            {"id": "p2_q3", "weight": 1.3, "critical": False,
             "text": "How effectively do HR, legal, DEI, and technology teams collaborate on HR AI design — with shared employee fairness and legal accountability?",
             "options": [(1,"Siloed — technology builds HR AI, HR receives it"),(2,"HR consulted at UAT only"),(3,"Some joint design for high-risk HR AI tools"),(4,"Integrated HR-legal-DEI-technology squads with shared fairness accountability"),(5,"Fully integrated HR AI squads with CHRO, legal counsel, DEI lead, and employee representative co-ownership of all people AI decisions")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the HR technology roadmap explicitly align AI investments to people strategy — DEI goals, skills-based workforce planning, remote work, and employee wellbeing?",
             "options": [(1,"HR technology roadmap built independently of people strategy"),(2,"Some AI tools referenced in HR plan"),(3,"HR AI roadmap mapped to people strategy but governed informally"),(4,"HR technology roadmap co-developed with CHRO, DEI, and legal leadership"),(5,"Real-time people strategy-technology alignment with AI as core of skills-based people platform")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal people outcome and fairness realisation framework tracking AI's impact on hiring quality, pay equity, retention, and DEI outcomes?",
             "options": [(1,"No post-deployment outcome tracking"),(2,"Anecdotal hiring manager feedback only"),(3,"Fairness review at 12 months for flagship tools only"),(4,"Formal people AI outcome framework with quarterly CHRO reporting"),(5,"Continuous people AI outcome attribution with real-time fairness monitoring, DEI disaggregation, and public pay equity reporting integrated with AI analytics")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of HR professionals, line managers, and employees have received AI literacy training — covering how HR AI tools work, their limitations, and employees' rights?",
             "options": [(1,"<5% — only HR systems specialists"),(2,"5–20% — mainly HR analytics and IT teams"),(3,"20–50% — HR business partners and some line managers"),(4,"50–80% — broad HR and line management coverage"),(5,">80% — universal coverage with role-specific AI literacy for HR, line managers, and all employees on their rights regarding AI in employment decisions")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI upskilling programme covering people analytics, AI fairness in hiring/performance, legal obligations, and human override responsibilities for HR professionals?",
             "options": [(1,"No programme — HR staff learn from vendors only"),(2,"Generic digital skills courses only"),(3,"Structured programme for HR analytics specialists only"),(4,"Broad programme covering HR business partners, DEI, legal, and line managers"),(5,"Comprehensive multi-tier programme with AI ethics in HR, algorithmic accountability modules, employment law AI content, and CIPD-accredited qualification integration")]},
            {"id": "p3_q3", "weight": 1.2, "critical": False,
             "text": "How strong is the culture of HR professionals and line managers critically reviewing AI hiring, performance, and pay recommendations rather than rubber-stamping them?",
             "options": [(1,"Very low — AI recommendations accepted without meaningful review"),(2,"Informal — some HR business partners question AI scores"),(3,"Moderate — HRBP review required for high-risk HR decisions (redundancy, termination)"),(4,"High — formal human review protocol for all AI-assisted employment decisions"),(5,"Exemplary — structured HR accountability framework with meaningful human review, employee right to explanation, AI override audit trail, and appeal mechanism for all AI-assisted people decisions")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have a People Analytics / AI in HR Centre of Excellence driving fair AI standards and building HR capability?",
             "options": [(1,"No CoE — each business unit buys its own HR AI tools"),(2,"Informal people analytics community with no mandate"),(3,"Small central people analytics team without CoE governance"),(4,"Established People Analytics CoE with HR AI governance and business engagement"),(5,"Mature CoE with federated model — embedded people analytics leads in each business unit with central fairness standards and works council interface")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage employee change from AI-driven HR processes — including employee concerns about surveillance, automated assessment, and job security?",
             "options": [(1,"No change management — HR AI deployed without employee consultation"),(2,"Policy announcement only"),(3,"Structured change management for major HR AI deployments"),(4,"Proactive employee engagement with works council and union consultation"),(5,"Comprehensive AI in HR workforce strategy with employee co-design, transparency portal, works council agreement, and employee AI rights charter integrated into employment contract")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": True,
             "text": "Does the organisation have a formally adopted AI in HR Ethics and Fairness Policy — covering algorithmic bias, employee data rights, transparency of AI decisions, and right to human review?",
             "options": [(1,"No HR AI ethics policy — general HR policy applied"),(2,"Data protection policy updated to mention AI"),(3,"Draft HR AI ethics policy not formally adopted"),(4,"Board-adopted HR AI fairness policy with employee transparency and review rights"),(5,"Comprehensive published AI in People charter with employee rights, DEI commitments, algorithmic transparency protocol, and annual independent fairness audit")]},
            {"id": "p4_q2", "weight": 1.4, "critical": True,
             "text": "Is there a systematic process for detecting and mitigating algorithmic bias in all AI-assisted employment decisions — hiring, performance, pay, promotion, and redundancy?",
             "options": [(1,"No bias testing for HR AI"),(2,"Ad hoc review when employment tribunal claim received"),(3,"Basic bias analysis for highest-risk HR decisions only (e.g., redundancy)"),(4,"Structured fairness assessment for all AI-assisted employment decisions with demographic disaggregation"),(5,"Automated continuous bias monitoring across all employment decisions with real-time DEI dashboards, EHRC engagement, and public pay equity reporting tied to AI analytics")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the HR AI regulatory compliance framework — covering UK GDPR/CCPA (employment data), EU AI Act (high-risk hiring AI), Equality Act, and worker monitoring regulations?",
             "options": [(1,"No awareness of AI-specific employment regulations"),(2,"Aware of GDPR and equality law but no HR AI-specific compliance programme"),(3,"Compliance underway for highest-risk HR AI (automated hiring, monitoring)"),(4,"Comprehensive compliance programme covering GDPR, EU AI Act, equality, and worker monitoring obligations"),(5,"Leading practice — proactive ICO/EHRC engagement, ahead of all HR AI requirements, and contributor to CIPD/CBI responsible people analytics standards")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there CHRO / Board oversight with named accountability for AI employment risk — including algorithmic bias, automated monitoring, and employee data protection?",
             "options": [(1,"No board visibility of HR AI employment risk"),(2,"AI risk mentioned generically in HR risk register"),(3,"CHRO receives periodic HR AI risk briefings"),(4,"People Committee with explicit HR AI risk oversight mandate"),(5,"Dedicated board AI in HR governance structure with CHRO/legal/works council joint accountability, external fairness auditor, and annual employment tribunal risk review")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply data minimisation, purpose limitation, and explicit employee consent to all AI systems using employee performance, engagement, and behavioural data?",
             "options": [(1,"No AI-specific employee data controls — general HR policy applied"),(2,"Standard GDPR applied without HR AI-specific safeguards"),(3,"HR AI data governance documented for key people analytics tools"),(4,"Formal HR AI data governance with explicit consent architecture, minimisation, and employee data access rights"),(5,"Privacy-by-design in all HR AI with employee data transparency portal, ICO engagement, works council data agreement, and real-time consent management for all people analytics")]},
        ],
    },

    # ── Cybersecurity Operations ─────────────────────────────────────────────
    "Cybersecurity operations": {
        1: [
            {"id": "p1_q1", "weight": 1.5, "critical": False,
             "text": "Does security leadership have a formally documented AI-augmented SOC strategy — covering AI threat detection, automated response, and human-AI analyst teaming — endorsed by the CISO and board?",
             "options": [(1,"No AI security strategy"),(2,"Informal AI security pilot discussions only"),(3,"Strategy draft not CISO/board-endorsed"),(4,"CISO/board-endorsed AI security strategy with detection rate and response time targets"),(5,"Comprehensive AI-augmented SOC strategy integrated into NIST/ISO 27001 security programme with board-level threat intelligence review")]},
            {"id": "p1_q2", "weight": 1.0, "critical": False,
             "text": "How frequently does the CISO or Security Board formally review AI threat detection performance — false positive rates, missed detections, adversarial robustness, and analyst workload?",
             "options": [(1,"Never — only when a breach occurs"),(2,"Annually in security review"),(3,"Quarterly security board review"),(4,"Monthly CISO review with AI SOC performance as standing agenda item"),(5,"Continuous real-time AI SOC dashboards with weekly CISO review, red team findings, and board threat briefing integration")]},
            {"id": "p1_q3", "weight": 1.2, "critical": False,
             "text": "Is there a dedicated AI Security / SOC Automation Lead with authority over AI threat detection tooling, SOAR integration, and human-AI analyst workflow design?",
             "options": [(1,"No dedicated role — AI decided by individual SOC managers"),(2,"AI security is a vendor-driven decision with no internal lead"),(3,"Named lead with limited tooling authority"),(4,"AI Security Lead with SOC tooling mandate and analyst workflow authority"),(5,"Head of AI Security Operations with CISO joint accountability, red team authority, and external AI security vendor management remit")]},
            {"id": "p1_q4", "weight": 1.0, "critical": False,
             "text": "How would you rate security leadership AI literacy — covering AI model adversarial robustness, AI-generated threats (deepfakes, AI phishing), and AI supply chain risk?",
             "options": [(1,"Very low — security leadership sees AI only as a detection tool"),(2,"Basic — aware of ML-based EDR and SIEM only"),(3,"Moderate — leadership understands adversarial ML, AI phishing, and AI SOC limitations"),(4,"Strong — security leadership actively governs AI threat detection quality and adversarial risk"),(5,"Exemplary — leadership drives AI security strategy, contributes to MITRE ATLAS/AI threat frameworks, and engages regulators on AI security standards")]},
            {"id": "p1_q5", "weight": 1.3, "critical": False,
             "text": "Does security leadership visibly champion AI as an analyst empowerment and detection quality priority — not just an alert volume tool?",
             "options": [(1,"No visible leadership commitment beyond vendor-claimed alert reduction"),(2,"AI referenced in SOC efficiency targets only"),(3,"Occasional commitment to AI-augmented SOC quality"),(4,"Regular CISO communication on AI as an analyst empowerment and threat coverage priority"),(5,"CISO-endorsed AI-augmented SOC programme with published detection quality, analyst wellbeing, and adversarial resilience KPIs")]},
        ],
        2: [
            {"id": "p2_q1", "weight": 1.5, "critical": False,
             "text": "Are AI security investments directly tied to measurable SOC KPIs — true positive rate, mean time to detect (MTTD), mean time to respond (MTTR), analyst alert fatigue reduction, and breach prevention rate?",
             "options": [(1,"No SOC KPIs defined for AI investments"),(2,"Vague 'efficiency improvement' goals without measurement"),(3,"KPIs defined for flagship AI security projects only"),(4,"Most AI security investments have tracked SOC KPI business cases"),(5,"All AI security investments governed by real-time SOC dashboards reviewed weekly by CISO with board-level threat and ROI reporting")]},
            {"id": "p2_q2", "weight": 1.2, "critical": False,
             "text": "How mature is the AI security tool portfolio governance — covering SIEM AI, EDR/XDR, SOAR, AI threat intelligence, and AI deception technology?",
             "options": [(1,"No formal process — security tools selected by individual analysts or vendors"),(2,"Informal prioritisation by security architects"),(3,"Basic tracking with some CISO input"),(4,"Formal AI security portfolio governance with threat landscape alignment and security business case"),(5,"Mature portfolio management with detection coverage mapping, vendor AI risk assessment, and dynamic tool rebalancing as threat landscape evolves")]},
            {"id": "p2_q3", "weight": 1.3, "critical": True,
             "text": "How effectively do SOC analysts, threat intelligence, incident response, and technology teams collaborate on AI tool design — ensuring AI enhances analyst judgment not replaces it?",
             "options": [(1,"Siloed — vendors design AI tools, analysts receive them"),(2,"Analysts consulted at tool deployment only"),(3,"Some joint design workshops for major AI security tools"),(4,"Co-design with SOC analysts embedded in AI security product development"),(5,"Fully integrated analyst-intelligence-IR-technology squads with shared detection quality and incident outcome accountability — analysts drive AI tool requirements and validation")]},
            {"id": "p2_q4", "weight": 1.0, "critical": False,
             "text": "Does the security technology roadmap explicitly prioritise AI investments aligned to threat landscape — zero-day AI detection, AI-generated attack surface management, insider threat AI?",
             "options": [(1,"Security roadmap built independently of current threat landscape"),(2,"Some AI tools referenced but not formally prioritised"),(3,"AI security roadmap mapped to threat priorities but governed informally"),(4,"Security roadmap co-developed with threat intelligence and SOC leadership"),(5,"Real-time threat-technology alignment with AI security as the core of the adaptive defence platform and board-level threat briefing input")]},
            {"id": "p2_q5", "weight": 1.0, "critical": False,
             "text": "Is there a formal ROI and threat reduction framework tracking AI value in security operations — including breach prevention value, analyst productivity, and false positive cost reduction?",
             "options": [(1,"No post-deployment SOC value tracking"),(2,"Anecdotal alert reduction claims at project close"),(3,"Detection rate review at 6 months only"),(4,"Formal AI security value framework with quarterly CISO reporting"),(5,"Continuous AI security value attribution with automated detection quality, analyst load, and breach prevention value modelling for board reporting")]},
        ],
        3: [
            {"id": "p3_q1", "weight": 1.2, "critical": False,
             "text": "What proportion of SOC analysts, security engineers, and IR teams have received advanced training on AI security tools — including AI output interpretation, adversarial awareness, and human override protocols?",
             "options": [(1,"<5% — only AI tool administrators"),(2,"5–20% — mainly data scientists embedded in security"),(3,"20–50% — AI tool users and some senior analysts"),(4,"50–80% — broad analyst and engineering coverage"),(5,">80% — universal coverage with role-specific AI augmentation training for all SOC analysts, IR specialists, and security engineers, including adversarial AI and AI tool failure mode awareness")]},
            {"id": "p3_q2", "weight": 1.3, "critical": False,
             "text": "Is there a structured AI security upskilling programme covering AI threat detection interpretation, adversarial ML awareness, AI-generated phishing/deepfake recognition, and AI tool limitations for security staff?",
             "options": [(1,"No programme — analysts rely on vendor training only"),(2,"Generic cybersecurity courses without AI-specific content"),(3,"Structured programme for AI tool administrators only"),(4,"Broad programme covering analysts, IR teams, and security engineers"),(5,"Comprehensive multi-tier programme with adversarial AI awareness, AI tool forensics, AI attack simulation, and CREST/SANS AI security specialisation content for all security roles")]},
            {"id": "p3_q3", "weight": 1.2, "critical": True,
             "text": "How strong is the culture of SOC analysts critically evaluating AI alerts and recommendations — exercising independent threat judgement and not deferring blindly to automated verdicts?",
             "options": [(1,"Very low — AI alerts actioned automatically without analyst review — dangerous dependency"),(2,"Informal — some senior analysts review, junior analysts automate"),(3,"Moderate — analyst review required for high-severity AI alerts"),(4,"High — formal analyst review protocol for all AI-generated high-risk threat verdicts"),(5,"Exemplary — structured human-AI threat analysis framework where analysts own all threat verdicts, with full override audit trail, AI confidence score transparency, and analyst feedback loop into AI model retraining")]},
            {"id": "p3_q4", "weight": 1.0, "critical": False,
             "text": "Does the organisation have an AI Security / Threat Intelligence Centre of Excellence driving AI SOC standards, red team adversarial testing, and analyst capability?",
             "options": [(1,"No CoE — each security team deploys its own AI tools"),(2,"Informal threat intelligence sharing group with no mandate"),(3,"Small central security engineering team without CoE structure"),(4,"Established AI Security CoE with SOC standards, red team mandate, and vendor engagement model"),(5,"Mature AI Security CoE with federated model — embedded AI security engineers across SOC, threat intel, IR, and red team with external academic research partnerships and threat sharing community leadership")]},
            {"id": "p3_q5", "weight": 1.3, "critical": False,
             "text": "How effectively does the organisation manage analyst change from AI-driven SOC automation — including analyst skill evolution, alert fatigue reduction, and career development in AI-augmented security?",
             "options": [(1,"No change management — AI deployed without analyst engagement"),(2,"Email announcement and vendor training only"),(3,"Structured change management for major AI SOC tool deployments"),(4,"Proactive analyst reskilling aligned to AI security roadmap with wellbeing monitoring"),(5,"Comprehensive AI-augmented SOC workforce strategy with analyst role redesign, wellbeing measurement, AI skill career pathways, and analyst co-design of AI tool interfaces and override protocols")]},
        ],
        4: [
            {"id": "p4_q1", "weight": 1.3, "critical": False,
             "text": "Does the organisation have a formal AI Security Governance Policy covering AI system attack surface, adversarial AI risk, AI model supply chain risk, and AI-generated threat response?",
             "options": [(1,"No AI security governance — general security policy applied to AI systems"),(2,"General network security policy referenced for AI systems"),(3,"Draft AI security governance policy not formally adopted"),(4,"Formally adopted AI security governance policy with adversarial risk assessment requirements"),(5,"Comprehensive AI security governance framework aligned to NIST AI RMF, MITRE ATLAS, and ISO/IEC 42001 with board-level AI attack surface review")]},
            {"id": "p4_q2", "weight": 1.4, "critical": True,
             "text": "Is there a systematic adversarial AI testing process — including red team AI model attacks, data poisoning simulation, and prompt injection testing — for all AI security tools before deployment?",
             "options": [(1,"No adversarial testing — AI tools deployed based on vendor security claims"),(2,"Ad hoc vendor-supplied penetration testing only"),(3,"Basic adversarial testing for highest-risk AI security tools"),(4,"Structured red team adversarial testing integrated into AI security tool procurement and deployment"),(5,"Formal AI red team programme with MITRE ATLAS adversarial scenarios, continuous adversarial monitoring, and real-world AI attack simulation for all AI systems in the security stack")]},
            {"id": "p4_q3", "weight": 1.3, "critical": False,
             "text": "How mature is the regulatory compliance framework for AI in cybersecurity — covering NIS2, DORA, EU AI Act (high-risk AI in critical infrastructure), and sector-specific AI security obligations?",
             "options": [(1,"No awareness of AI-specific cybersecurity regulations"),(2,"Aware of NIS2 and DORA but no AI-specific programme"),(3,"Compliance underway for most critical AI security regulations"),(4,"Comprehensive compliance programme covering NIS2, DORA, EU AI Act, and sector AI security obligations"),(5,"Leading practice — proactive engagement with NCSC/ENISA, ahead of all AI security regulatory requirements, and contributor to sector AI security standards")]},
            {"id": "p4_q4", "weight": 1.2, "critical": False,
             "text": "Is there Board / CISO oversight with named accountability for AI security risk — including AI system attack surface, AI supply chain risk, and AI-generated adversarial threats?",
             "options": [(1,"No board visibility of AI security risk"),(2,"AI security mentioned generically in risk register"),(3,"Board receives periodic AI security risk briefings"),(4,"Board Risk Committee with explicit AI security risk oversight mandate"),(5,"Dedicated board AI security governance structure with CISO/CRO joint accountability, external AI security advisor, and AI threat intelligence briefing integrated into board cyber dashboard")]},
            {"id": "p4_q5", "weight": 0.8, "critical": False,
             "text": "Does the organisation apply AI supply chain security controls — including AI model provenance verification, third-party AI API risk assessment, and AI training data integrity assurance?",
             "options": [(1,"No AI supply chain security controls"),(2,"Standard supplier vetting applied without AI-specific controls"),(3,"AI supply chain risk documented for highest-risk tools"),(4,"Formal AI supply chain security framework with model provenance and third-party API risk assessment"),(5,"Comprehensive AI supply chain security programme with model signing, training data integrity verification, continuous third-party AI API monitoring, and SBOM equivalent for all AI components")]},
        ],
    },
}  # end _IND_QUESTIONS


def get_dynamic_questions(industry: str) -> Dict[int, dict]:
    """
    Return the fully industry-specific question bank for the given industry.
    Falls back to the universal PILLAR_QUESTIONS if the industry is not found.
    Questions are returned in the canonical pillar structure with title & icon
    inherited from PILLAR_QUESTIONS so the UI can display them without changes.
    """
    if industry not in _IND_QUESTIONS:
        return copy.deepcopy(PILLAR_QUESTIONS)

    result: Dict[int, dict] = {}
    for pillar_num in range(1, 5):
        result[pillar_num] = {
            "title": PILLAR_QUESTIONS[pillar_num]["title"],
            "icon":  PILLAR_QUESTIONS[pillar_num]["icon"],
            "questions": copy.deepcopy(_IND_QUESTIONS[industry][pillar_num]),
        }
    return result


# ---------------------------------------------------------------------------
# Score Calculation  — 4-Layer Advanced Engine
# ---------------------------------------------------------------------------
#
# Layer 1: Weighted raw score     (same formula as before)
# Layer 2: Industry pillar mult.  (applied per-pillar before normalisation)
# Layer 3: Critical question cap  (if any critical Q scores ≤ 2, pillar capped at 7.0)
# Layer 4: Synergy bonus          (if both pillars in a pair score ≥ 7.5, each +0.3)
#
# Overall score: industry-weighted average of pillar scores (not simple mean)


def calculate_pillar_score(
    pillar_num: int,
    answers: Dict[str, int],
    industry: str = "Not specified",
    apply_multiplier: bool = False,
) -> float:
    """
    Calculate the weighted, normalised score (0–10) for a single CISLF pillar.

    Args:
        pillar_num:        1 to 4.
        answers:           Dict mapping question_id → selected rating (1-5).
        industry:          Industry string — used to fetch critical question list.
        apply_multiplier:  If True, multiply the normalised score by the industry
                           pillar weight (used only in calculate_all_scores).

    Returns:
        Float pillar score in range [0.0, 10.0], rounded to 1 decimal place.
    """
    # Use the industry-specific question bank to get correct weights/IDs
    dq = get_dynamic_questions(industry)
    questions = dq[pillar_num]["questions"]

    total_weighted = 0.0
    total_weight   = 0.0
    for q in questions:
        qid    = q["id"]
        weight = q["weight"]
        value  = float(answers.get(qid, 1))   # default 1 if unanswered
        total_weighted += value * weight
        total_weight   += weight

    if total_weight == 0:
        return 0.0

    max_possible = 5.0 * total_weight
    raw_score    = (total_weighted / max_possible) * 10.0
    raw_score    = min(raw_score, 10.0)

    # ── Layer 3: critical question penalty cap ─────────────────────────────
    cfg = INDUSTRY_SCORING_CONFIG.get(industry, {})
    critical_ids = cfg.get("critical_questions", [])
    # Map question IDs in the industry bank (IDs kept same format p{n}_q{n})
    for q in questions:
        if q.get("critical") and q["id"] in critical_ids:
            if answers.get(q["id"], 1) <= 2:
                raw_score = min(raw_score, 7.0)
                break

    # ── Layer 2: industry pillar multiplier ───────────────────────────────
    if apply_multiplier and cfg:
        pillar_weights = cfg.get("pillar_weights", {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0})
        raw_score = raw_score * pillar_weights.get(pillar_num, 1.0)

    return round(min(raw_score, 10.0), 1)


def calculate_all_scores(
    answers: Dict[str, int],
    industry: str = "Not specified",
) -> Tuple[Dict[int, float], float, Dict]:
    """
    Calculate scores for all four pillars and the overall CISLF score.

    Applies the full 4-layer scoring engine:
      1. Weighted raw score per pillar
      2. Industry pillar multiplier (normalised so overall range stays 0-10)
      3. Critical question hard cap (pillar capped at 7.0 if critical Q ≤ 2)
      4. Synergy bonus (+0.3 per pillar in a synergistic pair that both score ≥ 7.5)

    Args:
        answers:  Dict mapping question_id → rating (1-5).
        industry: Industry string.

    Returns:
        Tuple of:
          - pillar_scores_dict: {1: float, 2: float, 3: float, 4: float}
            (pre-synergy, post-multiplier, post-cap values)
          - overall_score: industry-weighted average, post-synergy (0-10)
          - breakdown: dict with scoring metadata for display
    """
    cfg = INDUSTRY_SCORING_CONFIG.get(industry, {})
    pillar_weights_raw = cfg.get("pillar_weights", {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0})
    synergy_pairs      = cfg.get("synergy_pairs", [])
    score_note         = cfg.get("score_note", "")
    critical_ids       = cfg.get("critical_questions", [])

    # ── Layers 1–3: base + critical cap (no multiplier yet) ────────────────
    base_scores: Dict[int, float] = {
        p: calculate_pillar_score(p, answers, industry, apply_multiplier=False)
        for p in range(1, 5)
    }

    # ── Layer 4: synergy bonus ─────────────────────────────────────────────
    applied_synergy: List[str] = []
    synergy_scores = dict(base_scores)
    for pa, pb in synergy_pairs:
        if base_scores.get(pa, 0) >= 7.5 and base_scores.get(pb, 0) >= 7.5:
            synergy_scores[pa] = round(min(synergy_scores[pa] + 0.3, 10.0), 1)
            synergy_scores[pb] = round(min(synergy_scores[pb] + 0.3, 10.0), 1)
            p_names = {
                1: "Leadership & Vision", 2: "Strategic Alignment",
                3: "Capability & Culture", 4: "Responsible Governance"
            }
            applied_synergy.append(
                f"Pillar {pa} ({p_names[pa]}) + Pillar {pb} ({p_names[pb]}) synergy +0.3"
            )

    # ── Industry-weighted overall score ────────────────────────────────────
    total_weight = sum(pillar_weights_raw.values())
    weighted_sum = sum(
        synergy_scores[p] * pillar_weights_raw.get(p, 1.0)
        for p in range(1, 5)
    )
    overall = round(min((weighted_sum / total_weight), 10.0), 1)

    # ── Detect which critical questions triggered caps ─────────────────────
    dq = get_dynamic_questions(industry)
    triggered_caps: List[str] = []
    for p in range(1, 5):
        for q in dq[p]["questions"]:
            if q.get("critical") and q["id"] in critical_ids:
                if answers.get(q["id"], 1) <= 2:
                    triggered_caps.append(
                        f"Pillar {p}: '{q['text'][:60]}...' scored ≤2 → pillar capped at 7.0"
                    )

    breakdown = {
        "industry":            industry,
        "pillar_weights":      pillar_weights_raw,
        "base_scores":         base_scores,
        "final_scores":        synergy_scores,
        "applied_synergy":     applied_synergy,
        "triggered_caps":      triggered_caps,
        "score_note":          score_note,
        "total_weight":        total_weight,
    }

    return synergy_scores, overall, breakdown



# ---------------------------------------------------------------------------
# Text Template Libraries
# ---------------------------------------------------------------------------
# Each template dict: {pillar_num: {(lo, hi): content}}
# Content types: str (assessment), List[str] (strengths/gaps/recommendations)

ASSESSMENT_TEXTS: Dict[int, Dict[BandKey, str]] = {
    1: {
        (0.0, 3.9): (
            "The organisation faces a critical leadership deficit in its AI transformation journey. "
            "The absence of a coherent AI vision, dedicated leadership accountability, and executive AI "
            "literacy creates a fundamental barrier to any sustainable transformation effort. Without "
            "immediate, visible leadership commitment, AI initiatives will continue to lack direction, "
            "resources, and the organisational buy-in needed for adoption at scale."
        ),
        (4.0, 5.4): (
            "Leadership awareness of AI's strategic importance is emerging, but remains inconsistent "
            "and largely unrealised in practice. Enthusiasm exists in pockets, yet the absence of a "
            "unified, communicated AI vision results in misalignment across business units. Executive "
            "AI literacy is insufficient to make confident, informed decisions about AI investments "
            "and risks, creating dependency on technical specialists."
        ),
        (5.5, 6.9): (
            "The organisation demonstrates a developing leadership posture for AI transformation. "
            "An AI vision is taking shape and some executive sponsorship is visible, signalling "
            "genuine intent. However, leadership AI literacy and top-down communication of the "
            "transformation agenda remain inconsistent. The gap between aspiration and embedded "
            "practice must be narrowed through sustained leadership investment."
        ),
        (7.0, 8.4): (
            "Leadership demonstrates strong, consistent commitment to AI-driven transformation. "
            "A clear AI vision is articulated and actively championed, with dedicated leadership "
            "structures providing accountability. Executives are increasingly AI-literate and "
            "personally invested in transformation outcomes. The foundation is solid — the focus "
            "should now shift to embedding AI leadership behaviours throughout the management pipeline."
        ),
        (8.5, 10.0): (
            "Leadership mindset and vision represent a genuine organisational strength and "
            "competitive differentiator. The executive team demonstrates exemplary AI leadership — "
            "a compelling, board-endorsed AI vision drives decision-making at all levels. Leaders "
            "are highly AI-literate, role-model adoption, and create the cultural conditions for "
            "bold, responsible AI transformation. This provides a powerful foundation for "
            "sustained competitive advantage."
        ),
    },
    2: {
        (0.0, 3.9): (
            "Strategic alignment between AI initiatives and business outcomes is critically weak. "
            "AI projects are being pursued in a technology-led vacuum, disconnected from measurable "
            "business value. Siloed working between business and technology functions amplifies "
            "this misalignment. Without urgent intervention to anchor AI investments to business "
            "strategy, the organisation risks significant resource waste and eroding confidence "
            "in AI as a strategic enabler."
        ),
        (4.0, 5.4): (
            "Business-technology alignment for AI is in early development with significant structural "
            "gaps. Some connection between AI projects and business objectives exists, but the absence "
            "of formal portfolio governance and ROI measurement means value is being left unrealised. "
            "A coherent AI investment framework and meaningful cross-functional collaboration are "
            "urgently needed to ensure AI expenditure delivers strategic returns."
        ),
        (5.5, 6.9): (
            "The organisation is building its strategic alignment capabilities, with AI initiatives "
            "increasingly connected to business priorities. Cross-functional collaboration is improving "
            "and portfolio management is emerging. However, inconsistency in applying business KPIs "
            "and ROI measurement across all AI investments means significant value remains at risk. "
            "Maturing these processes is the critical next step."
        ),
        (7.0, 8.4): (
            "Strong strategic alignment is evident, with the majority of AI initiatives tied to "
            "business KPIs and supported by effective cross-functional delivery structures. Portfolio "
            "governance is providing meaningful oversight and investment discipline. Focus should "
            "now shift to real-time alignment mechanisms and advanced benefits realisation to "
            "maximise the full return on the AI portfolio."
        ),
        (8.5, 10.0): (
            "The organisation exemplifies strategic business-technology alignment for AI. Every "
            "AI investment is anchored to clearly defined strategic outcomes, governed through a "
            "sophisticated portfolio process, and co-owned by business and technology functions. "
            "This alignment capability enables rapid, confident AI investment decisions and "
            "represents a durable source of competitive advantage."
        ),
    },
    3: {
        (0.0, 3.9): (
            "Organisational capability and cultural readiness for AI transformation are at a critical "
            "deficit. The workforce lacks foundational AI literacy, structured upskilling programmes "
            "are absent, and a risk-averse culture actively inhibits the experimentation necessary "
            "for AI innovation. Without immediate, substantial investment in people capability and "
            "cultural change, the organisation's capacity to adopt and scale AI remains severely "
            "constrained regardless of technology investments made."
        ),
        (4.0, 5.4): (
            "AI capability and cultural readiness are developing, but significant gaps persist across "
            "most dimensions. Skills shortages — both technical and non-technical — create adoption "
            "bottlenecks and increase dependency on external vendors. Limited psychological safety "
            "constrains the innovation essential for AI learning. Structured upskilling and "
            "deliberate cultural interventions are needed at scale to create the human foundation "
            "for successful AI deployment."
        ),
        (5.5, 6.9): (
            "Meaningful progress is evident in building AI capability and a supportive culture. "
            "Upskilling programmes are underway and experimentation is increasingly encouraged in "
            "parts of the organisation. The priority now is consistency and scale — AI capability "
            "remains uneven across business units and hierarchy levels. A systematic approach "
            "to federating AI skills and embedding a learning culture organisation-wide is required."
        ),
        (7.0, 8.4): (
            "Strong organisational capability and a positive AI culture are clear organisational "
            "strengths. Upskilling programmes are active and reaching a broad workforce population. "
            "A culture of experimentation is taking hold with visible leadership role-modelling. "
            "Investment should now focus on advanced capability development, federated AI roles in "
            "business units, and systematic AI talent retention."
        ),
        (8.5, 10.0): (
            "The organisation demonstrates exemplary AI capability and culture — a rare and powerful "
            "competitive asset. A comprehensive, multi-tiered upskilling ecosystem, high psychological "
            "safety, and a mature, federated CoE model create an unparalleled human foundation for "
            "AI transformation. The organisation's people are its strongest AI differentiator and "
            "should be treated as a strategic asset to protect and amplify."
        ),
    },
    4: {
        (0.0, 3.9): (
            "Responsible AI governance is critically underdeveloped, representing the organisation's "
            "most significant risk exposure. The absence of AI ethics policies, bias detection "
            "processes, regulatory compliance frameworks, and board-level oversight creates severe "
            "legal, reputational, and operational risk. Any further scaling of AI deployments without "
            "foundational governance infrastructure represents an unacceptable organisational risk."
        ),
        (4.0, 5.4): (
            "AI governance awareness is growing but action significantly lags behind. Basic compliance "
            "activities exist, primarily extending general IT policies to AI contexts — insufficient "
            "for the specific risks AI introduces. Board visibility of AI risk is limited. The "
            "governance maturity must accelerate substantially to keep pace with the organisation's "
            "AI adoption ambitions and the evolving regulatory environment."
        ),
        (5.5, 6.9): (
            "Responsible AI governance is developing with increasing structure emerging around "
            "ethics, compliance, and risk management. Board visibility of AI risk is improving "
            "and key policies are taking shape. Critical gaps remain in automated bias monitoring, "
            "privacy-by-design, and comprehensive regulatory readiness. Formalising, scaling, "
            "and systematising governance processes is the immediate priority."
        ),
        (7.0, 8.4): (
            "Strong responsible AI governance practices are in place, providing meaningful protection "
            "and enabling confident AI deployment. Ethics policies are formalised, bias assessment "
            "processes are integrated into the development lifecycle, and board oversight structures "
            "are established. The organisation is well-positioned for the evolving regulatory "
            "landscape. Focus should shift to automation of governance and proactive regulatory leadership."
        ),
        (8.5, 10.0): (
            "Responsible AI governance represents a true organisational strength and a benchmark "
            "for the industry. Comprehensive ethics frameworks, automated bias monitoring, proactive "
            "regulatory engagement, and robust board accountability provide the confidence to scale "
            "AI responsibly and at speed. The organisation's governance maturity is a competitive "
            "advantage that enables bold AI ambition with institutional trust."
        ),
    },
}

STRENGTH_TEXTS: Dict[int, Dict[BandKey, List[str]]] = {
    1: {
        (0.0, 3.9): ["Initial executive-level interest in AI is beginning to emerge", "Some recognition of AI's strategic importance exists at leadership level", "Openness to engaging in leadership capability development for AI"],
        (4.0, 5.4): ["Growing executive awareness of AI transformation opportunities", "Some leadership capacity dedicated to AI agenda is emerging", "Informal AI strategy discussions occurring at senior levels"],
        (5.5, 6.9): ["Documented AI vision under active development", "Named executive sponsors identified for key AI initiatives", "Leadership AI literacy improvement programmes have been initiated"],
        (7.0, 8.4): ["Clear and widely communicated AI transformation vision", "Strong executive sponsorship with personal commitment from C-suite", "Dedicated AI leadership role with mandate and budget authority"],
        (8.5, 10.0): ["Exemplary, board-endorsed AI vision driving organisation-wide decisions", "Highly AI-literate executive team actively shaping AI strategy", "AI thinking fully embedded in all strategic planning and governance cycles"],
    },
    2: {
        (0.0, 3.9): ["Some individual AI proof-of-concept success stories provide a reference base", "Technology infrastructure provides a technical foundation for AI", "IT team possesses growing AI technical awareness"],
        (4.0, 5.4): ["Business stakeholders are increasingly aware of AI's potential value", "Informal AI-business collaboration is beginning to emerge", "Technology roadmap includes AI components as recognised priorities"],
        (5.5, 6.9): ["Business KPIs are being defined for a growing proportion of AI initiatives", "Cross-functional collaboration is improving with fewer departmental barriers", "AI portfolio management process is in development"],
        (7.0, 8.4): ["Majority of AI initiatives are anchored to measurable business KPIs", "Effective cross-functional AI delivery structures are operational", "Formal AI portfolio governance process is delivering investment discipline"],
        (8.5, 10.0): ["All AI investments are tied to strategic business outcomes with real-time tracking", "Exemplary business-technology integration with co-ownership of AI results", "Sophisticated portfolio governance enabling dynamic investment rebalancing"],
    },
    3: {
        (0.0, 3.9): ["Motivated AI champions exist informally in parts of the organisation", "Some technical AI expertise is present in the IT function", "Leadership acknowledgement that capability development is needed"],
        (4.0, 5.4): ["Technical AI capability exists in pockets across the organisation", "Some upskilling initiatives have been started or are planned", "Growing management awareness of the culture change AI requires"],
        (5.5, 6.9): ["Structured upskilling programme is operational and expanding", "AI Centre of Excellence or equivalent is forming with initial mandate", "Experimentation culture is growing visibly in some teams or units"],
        (7.0, 8.4): ["Broad AI literacy programme reaching majority of the workforce", "Established AI CoE with clear business engagement and delivery model", "Strong culture of experimentation with leadership role-modelling"],
        (8.5, 10.0): ["Comprehensive multi-tier AI capability ecosystem from awareness to expert level", "Mature, federated CoE model with AI practitioners embedded in all business units", "Exemplary psychological safety enabling bold AI experimentation"],
    },
    4: {
        (0.0, 3.9): ["General data governance and security framework provides a base to build on", "Existing risk management culture means infrastructure for AI governance exists", "Regulatory compliance function can be extended to AI-specific requirements"],
        (4.0, 5.4): ["General compliance practices are beginning to be applied to AI contexts", "Growing internal awareness of AI-specific risks is creating governance momentum", "Ethics discussions have been initiated, creating a foundation for formal policy"],
        (5.5, 6.9): ["AI ethics policy is in active development with stakeholder engagement", "Bias testing is being applied to the highest-risk AI models", "Board is receiving AI risk information with growing frequency and depth"],
        (7.0, 8.4): ["Formal, adopted AI ethics policy with board endorsement", "Structured bias assessment integrated into AI development lifecycle", "Clear board governance structure with AI risk oversight mandate"],
        (8.5, 10.0): ["Leading AI ethics and governance practice setting an industry benchmark", "Automated bias monitoring with continuous fairness metrics and full audit trail", "Proactive regulatory engagement, ahead of compliance requirements"],
    },
}

GAP_TEXTS: Dict[int, Dict[BandKey, List[str]]] = {
    1: {
        (0.0, 3.9): ["Complete absence of a formal, documented AI vision and transformation strategy", "No dedicated AI leadership role — accountability is diffuse and unclear", "Critical gap in executive AI literacy preventing informed decision-making"],
        (4.0, 5.4): ["AI vision exists in name but is not consistently communicated or operationalised", "Insufficient executive AI literacy to make confident, independent AI decisions", "No structured leadership development programme to build AI capability at the top"],
        (5.5, 6.9): ["AI vision not yet fully embedded into organisational culture and daily decision-making", "Leadership AI literacy deepening required — executives still rely heavily on specialists", "Executive sponsorship inconsistent across AI initiatives, creating priority uncertainty"],
        (7.0, 8.4): ["AI thinking not yet fully integrated into all strategic decisions as a default lens", "Leadership development pipeline for AI not systematically built across the organisation", "Board-level AI governance and oversight could be further formalised and strengthened"],
        (8.5, 10.0): ["Maintaining AI vision relevance as the technology landscape evolves at pace", "AI leadership succession planning needed to protect organisational capability", "Extending AI leadership culture to acquired entities and ecosystem partners"],
    },
    2: {
        (0.0, 3.9): ["No formal AI portfolio management or investment governance process exists", "Business and technology functions operating in silos with no shared AI accountability", "AI projects lack defined business KPIs — value realisation cannot be measured"],
        (4.0, 5.4): ["Inconsistent linkage between AI projects and business outcomes undermining ROI", "Cross-functional collaboration remains fragmented with significant organisational friction", "No formal ROI framework — AI investment value is unmeasured and unjustifiable"],
        (5.5, 6.9): ["Portfolio management process not yet mature enough to optimise investment decisions", "Cross-functional accountability mechanisms still developing — ownership is sometimes unclear", "Business case quality is variable across AI investments — inconsistent standards applied"],
        (7.0, 8.4): ["Real-time business-technology alignment mechanisms not yet in place", "Benefits realisation measurement could be more rigorous and consistently applied", "AI portfolio optimisation opportunities across the full investment landscape not fully exploited"],
        (8.5, 10.0): ["Maintaining alignment speed as the AI opportunity landscape evolves rapidly", "Extending alignment and governance model to ecosystem partners and suppliers", "Dynamic portfolio rebalancing as AI capabilities and market needs mature"],
    },
    3: {
        (0.0, 3.9): ["Severely limited AI literacy across the workforce creates widespread adoption barriers", "Complete absence of a structured upskilling or reskilling programme for AI", "Culture that penalises failure makes AI experimentation and learning impossible"],
        (4.0, 5.4): ["Significant AI skills gaps across both technical and non-technical workforce segments", "Upskilling insufficient in both scale (reaching few) and scope (technical only)", "Change management capability for AI adoption is underdeveloped and underresourced"],
        (5.5, 6.9): ["Upskilling programme not yet reaching all workforce segments and seniority levels consistently", "AI CoE model is not yet federated into business units — central, not embedded", "Adoption metrics for AI deployments not systematically defined or tracked"],
        (7.0, 8.4): ["Advanced AI capability not yet distributed evenly across all business units", "AI talent retention at risk in a competitive and constrained talent market", "Upskilling programme not yet fully aligned to future AI skill needs (e.g., agentic AI)"],
        (8.5, 10.0): ["Sustaining capability development pace with the rapid evolution of AI technology", "AI talent ecosystem dependency risks need proactive management", "Knowledge management across distributed AI capability requires systematic attention"],
    },
    4: {
        (0.0, 3.9): ["No AI ethics policy, governance framework, or accountability structure", "Bias detection completely absent from AI development and deployment processes", "No board visibility or accountability for AI risk — significant governance void"],
        (4.0, 5.4): ["AI ethics policy is absent or wholly inadequate for AI-specific risks", "AI regulatory compliance not systematically managed — significant exposure risk", "Board AI risk oversight is informal or absent — accountability is unclear"],
        (5.5, 6.9): ["AI ethics policy not yet formally adopted, embedded, or enforced organisation-wide", "Bias mitigation is not systematic — only highest-risk models tested, not all AI systems", "Privacy-by-design is not yet embedded in AI development practices organisation-wide"],
        (7.0, 8.4): ["Automated AI governance processes are not yet fully operational at scale", "Proactive regulatory engagement strategy has not yet been established", "AI governance culture not yet pervasive — compliance seen as a check, not a value"],
        (8.5, 10.0): ["Maintaining governance pace with rapidly emerging AI regulations globally", "Extending responsible AI governance framework to AI ecosystem partners and vendors", "Quantifying and communicating the business value of AI governance to all stakeholders"],
    },
}

RECOMMENDATION_TEXTS: Dict[int, Dict[BandKey, List[str]]] = {
    1: {
        (0.0, 3.9): [
            "Commission a CEO-sponsored executive AI visioning workshop within 30 days — produce a board-endorsed AI transformation vision statement as an immediate deliverable",
            "Appoint a Chief AI Officer or equivalent C-suite AI leader immediately, with explicit mandate, dedicated budget, and a direct reporting line to the CEO or board",
            "Launch a 6-month executive AI literacy development programme combining external expert coaching, peer benchmarking, and structured AI use case exploration",
        ],
        (4.0, 5.4): [
            "Develop and cascade a formal AI transformation strategy document to all organisational levels within 60 days, including a 3-year roadmap with measurable milestones",
            "Establish a structured executive AI learning journey incorporating site visits to AI-leading organisations and facilitated expert roundtables",
            "Create high-visibility leadership AI sponsorship mechanisms — CEO town halls on AI progress, AI success showcases, and regular strategic communications",
        ],
        (5.5, 6.9): [
            "Embed AI as a standing agenda item in all executive and board meetings to normalise strategic AI discussion and decision-making at the top",
            "Develop leadership-specific AI use cases and pilot projects to deepen executive understanding through direct experience rather than briefings alone",
            "Establish an Executive AI Advisory Board combining internal leaders with 3-5 external AI experts to accelerate leadership development and challenge assumptions",
        ],
        (7.0, 8.4): [
            "Integrate AI literacy metrics into executive onboarding and performance management frameworks to sustain and deepen leadership capability systematically",
            "Develop an AI Leadership Excellence model to identify and invest in next-generation AI leaders two to three levels below the C-suite",
            "Create a visible external AI thought leadership presence through publications, conference keynotes, and regulatory engagement to attract AI talent and signal strategic intent",
        ],
        (8.5, 10.0): [
            "Build a formal AI leadership succession pipeline to protect organisational capability against talent loss or leadership transition",
            "Establish academic and research institution partnerships to co-develop next-generation AI leadership frameworks aligned with emerging AI capabilities",
            "Create an industry AI leadership forum to share learnings and actively shape regulatory, standards, and ethics conversations in your sector",
        ],
    },
    2: {
        (0.0, 3.9): [
            "Immediately reset the AI portfolio — pause all projects without defined business outcomes and require business-led resubmission through a formal investment framework within 45 days",
            "Establish a joint Business-Technology AI Steering Committee with equal representation, shared accountability for outcomes, and CEO-level sponsorship",
            "Implement a mandatory AI Investment Framework within 45 days covering business case standards, KPI definition, ROI measurement, and stage-gate governance requirements",
        ],
        (4.0, 5.4): [
            "Develop a formal AI-to-strategy alignment map within 60 days, linking every AI initiative explicitly to a specific strategic objective and trackable business metric",
            "Launch co-led cross-functional delivery squads for the top 5 AI priorities, with named business and technology owners sharing P&L accountability",
            "Implement quarterly AI portfolio reviews chaired by the CEO or COO to assess value delivery and dynamically reprioritise based on strategic outcomes",
        ],
        (5.5, 6.9): [
            "Mature the AI portfolio governance process with defined stage gates, active benefits tracking, and executive-level RAG status reporting on all major programmes",
            "Develop a comprehensive AI ROI measurement framework covering financial, operational, customer experience, and strategic option value dimensions",
            "Create embedded AI Business Partner roles within each major business unit to maintain real-time alignment between technology delivery and business need",
        ],
        (7.0, 8.4): [
            "Implement real-time AI portfolio performance dashboards giving executives continuous visibility of AI investment performance against strategic business KPIs",
            "Develop dynamic AI portfolio rebalancing capability — a formal process to shift investment rapidly in response to strategic shifts or market changes",
            "Extend the alignment framework to ecosystem partners and strategic vendors to ensure AI investments across the value chain are aligned to shared outcomes",
        ],
        (8.5, 10.0): [
            "Create an AI Market Sensing capability to continuously identify, evaluate, and size emerging AI opportunities against strategic priorities for portfolio inclusion",
            "Develop formal AI M&A evaluation criteria to assess acquisition targets for AI capability fit, portfolio alignment, and transformation potential",
            "Establish an AI Value Architecture review to optimise the full portfolio of AI assets — models, data, platforms, and talent — for maximum strategic and financial return",
        ],
    },
    3: {
        (0.0, 3.9): [
            "Launch an emergency AI literacy programme with a commitment to reach 100% of management population and 50% of all staff within 6 months — funded and sponsored by CEO",
            "Establish a dedicated AI Centre of Excellence immediately with a formal mandate, ring-fenced funding, and a senior leader as Director reporting to the CAIO or CTO",
            "Implement a deliberate psychological safety programme beginning with visible leadership modelling of failure-positive behaviours and AI experimentation storytelling",
        ],
        (4.0, 5.4): [
            "Design and launch a multi-tier AI Skills Framework within 90 days, covering awareness, practitioner, and expert levels with role-specific learning pathways for all functions",
            "Establish a ringfenced AI Experimentation Fund — minimum 10% of total AI budget — dedicated to low-risk innovation sprints with a fast-fail governance model",
            "Deploy a structured AI Change Management methodology for all AI deployments, tracking adoption rates as formal project success metrics from go-live day one",
        ],
        (5.5, 6.9): [
            "Scale AI upskilling to reach all business units and seniority levels, with role-specific learning pathways, internal certification recognition, and career pathway linkage",
            "Federate the AI CoE model by embedding dedicated AI Coaches and Practitioners in each major business unit, moving from a central service to an embedded capability",
            "Introduce AI adoption KPIs — active usage rates, value per deployment — into team and individual leader performance scorecards to drive accountable adoption",
        ],
        (7.0, 8.4): [
            "Develop advanced AI specialisation tracks for high-potential employees in partnership with leading universities or specialist training providers with formal accreditation",
            "Implement an AI Talent Marketplace to optimise the deployment of scarce advanced AI skills across the portfolio based on strategic priority and impact potential",
            "Create a certified AI Ambassador Network to propagate AI culture, identify use cases, and support adoption through a peer-to-peer influence model across all locations",
        ],
        (8.5, 10.0): [
            "Establish external AI capability partnerships with academia, startups, and research institutes to maintain a permanent learning and innovation edge beyond internal capacity",
            "Develop a compelling AI Talent Brand — published through case studies, media, and employer recognition awards — to attract world-class AI professionals at all levels",
            "Create a structured AI Community Contribution Programme allowing employees to contribute to open-source AI projects, building external reputation and internal pride",
        ],
    },
    4: {
        (0.0, 3.9): [
            "Establish a foundational responsible AI governance framework as an immediate prerequisite for any further AI deployment — including an ethics policy, bias review process, and data privacy standards — all adopted within 60 days",
            "Appoint a dedicated AI Ethics and Governance Lead with a board-level reporting line and mandate to build comprehensive governance infrastructure within 90 days",
            "Commission an urgent AI Risk Audit across all current AI deployments to identify and immediately mitigate the most critical ethical, compliance, and operational risks",
        ],
        (4.0, 5.4): [
            "Develop and formally adopt a comprehensive, AI-specific Ethics Policy with full board endorsement and a public organisational commitment within 90 days",
            "Implement structured, mandatory AI Bias Assessments as a non-negotiable development lifecycle step for all models that affect individual or customer decisions",
            "Establish a Board AI Risk Committee or formally extend the existing Risk Committee mandate to include explicit AI-specific risk categories and reporting obligations",
        ],
        (5.5, 6.9): [
            "Integrate Privacy-by-Design principles into all AI development processes, with mandatory Data Protection Impact Assessments as a gate for all new AI system launches",
            "Develop a comprehensive AI Regulatory Compliance Roadmap covering current obligations (GDPR, sector rules) and emerging requirements (EU AI Act, international standards)",
            "Implement automated AI monitoring tools for bias detection, model performance drift, and compliance alerting across all AI systems operating in production",
        ],
        (7.0, 8.4): [
            "Establish a proactive regulatory engagement strategy — actively participating in regulatory consultations, standards bodies, and industry working groups to shape the AI governance landscape",
            "Develop an annual AI Governance Transparency Report for both internal stakeholders and external audiences to build institutional trust and demonstrate responsible AI leadership",
            "Extend the governance framework to the AI supply chain — formally assess AI vendors and partners for responsible AI compliance as a procurement requirement",
        ],
        (8.5, 10.0): [
            "Develop industry-leading AI governance thought leadership through white papers, regulatory submissions, and academic collaboration to define best practice for the sector",
            "Implement AI Governance-as-a-Platform — automated, real-time governance monitoring with predictive compliance intelligence and automated incident response workflows",
            "Establish an independent AI Ethics Advisory Board with external domain experts, civil society representation, and an annual published review of AI governance performance",
        ],
    },
}


# ---------------------------------------------------------------------------
# Action Plan Templates (keyed by overall score band)
# ---------------------------------------------------------------------------

ACTION_PLAN_TEXTS: Dict[BandKey, Dict[str, List[str]]] = {
    (0.0, 3.9): {
        "month1": [
            "Establish an Emergency AI Governance Task Force with CEO sponsorship: Assemble a joint team of IT, legal, and business leads. Audit all active departments to identify shadow AI tools, classify risk profiles, and issue immediate security controls or usage halts where data privacy is exposed.",
            "Commission a comprehensive CISLF AI Maturity Assessment: Collaborate with an external advisory partner to baseline capabilities across leadership, alignment, capability, and governance. Create a gap report to prioritize quick wins and long-term milestones.",
            "Implement a mandatory pause on unmanaged AI projects: Set a strict 30-day deadline requiring all active AI initiatives to submit a standardized business case showing executive sponsorship, target metrics (ROI, time-savings), and safety checks."
        ],
        "month2": [
            "Launch an Executive AI Literacy Sprint: Conduct a 4-week facilitated program (2 hours weekly) for the C-suite and board. Cover AI capabilities, risk structures, and strategic investment frameworks, culminating in a signed corporate AI vision statement.",
            "Draft the Corporate AI Ethics Policy and Investment Framework: Define bias validation thresholds, data privacy rules, and stage-gate approval criteria. Circulate the draft to all department heads for operational feedback.",
            "Initiate an AI Upskilling Pilot: Train a cohort of 100 frontline employees in high-impact areas (e.g., customer service, IT) on basic prompt engineering and data security guidelines to test training modules."
        ],
        "month3": [
            "Adopt the AI Ethics Policy and Investment Gateways: Formally approve the policies at the board level. Embed governance checks directly into the procurement and DevOps pipelines so no software is bought/deployed without verification.",
            "Establish the foundational AI Centre of Excellence (CoE): Recruit an AI Director and core team (1 data scientist, 1 business analyst, 1 project manager). Approve a charter, engagement model, and 12-month delivery roadmap.",
            "Re-launch the reprioritised AI portfolio: Release funding for paused projects that successfully pass the new governance gate. Ensure each has a named business owner and technology owner to co-manage delivery."
        ],
    },
    (4.0, 5.4): {
        "month1": [
            "Conduct a Strategic AI Gap Analysis: Map all current AI initiatives against corporate business objectives. Run mapping workshops with department leads to identify duplications, resource bottlenecks, and projects with low strategic value.",
            "Facilitate a Leadership AI Vision Workshop: Run a structured alignment session for senior executives. Define the organization's strategic posture on AI (e.g., fast follower vs. pioneer) and draft a 3-year transformation roadmap with board-level funding targets.",
            "Design the Enterprise AI Skills Framework: Define required AI competencies across different job tiers (executive, manager, technical, general staff). Design a modular training curriculum and obtain budget approval for a scaled upskilling roll-out."
        ],
        "month2": [
            "Establish AI Portfolio Stage-Gate Governance: Implement a formal gate-review process. Require all AI projects to present business KPI targets, data availability certificates, and risk reviews before moving from pilot to development.",
            "Stand up cross-functional AI Delivery Squads: Form dedicated pods for the top 3 high-priority initiatives. Include a product owner, data engineer, compliance officer, and frontline business users to co-create solutions.",
            "Roll out Management-level AI Literacy Training: Launch the foundational training program for all team leaders and managers. Focus on identifying AI use cases, managing change, and understanding ethical and privacy risks."
        ],
        "month3": [
            "Formalise the AI Governance Framework: Publish the AI Ethics Policy, algorithmic bias review guidelines, and compliance tracking procedures. Appoint an AI Ethics Officer to lead evaluations.",
            "Launch the AI Centre of Excellence (CoE) Hub: Approve the CoE service catalogue, defining how business units request assistance, build prototypes, and access shared data resources. Launch the internal CoE portal.",
            "Publish the Enterprise AI Transformation Roadmap: Share the 3-year commitments, key milestones, and upskilling opportunities with all staff via a CEO-led town hall. Establish a public feedback channel for questions."
        ],
    },
    (5.5, 6.9): {
        "month1": [
            "Embed AI Transformation into Board Governance: Add progress tracking against the CISLF roadmap as a standing agenda item in executive and board risk committee meetings. Update annual strategic goals to include AI KPIs.",
            "Deploy an Automated AI Investment Dashboard: Build a tracking dashboard showing real-time spend, pilot success rates, time-to-market, and business value delivery across the portfolio. Make it visible to all executive sponsors.",
            "Scale the AI Upskilling Programme: Roll out role-specific learning paths (e.g., AI in HR, AI in Finance) to 50% of the workforce. Embed completion rates directly into quarterly management performance reviews."
        ],
        "month2": [
            "Deploy the Federated AI CoE Operating Model: Embed dedicated AI specialists directly into the major business units (e.g., Marketing, Ops). Maintain a hub-and-spoke model where they share best practices with the central CoE.",
            "Implement Mandatory Algorithmic Bias Testing: Integrate automated bias validation tools into the CI/CD deployment pipelines. Enforce mathematical fairness checks as a non-negotiable deployment gate.",
            "Establish Monthly Business-Technology Outcomes Reviews: Host structured, joint reviews where technology and business team leaders review active AI system adoption rates, value metrics, and user feedback."
        ],
        "month3": [
            "Deploy Continuous Production Monitoring Tools: Implement monitoring systems to detect model accuracy decay, data drift, and unexpected outcomes in live production environments, linked to automated alert systems.",
            "Establish a Structured AI Experimentation Framework: Define a fast-fail innovation process with a ringfenced budget. Allow teams to run rapid, low-cost 2-week proofs-of-concept with minimal administrative overhead.",
            "Publish the Internal AI Maturity Progress Report: Share an honest, transparent assessment of roadmap execution, capability building, and governance compliance with the entire workforce to maintain momentum."
        ],
    },
    (7.0, 8.4): {
        "month1": [
            "Conduct an AI Leadership Excellence Review: Evaluate capability, capacity, and mindset among senior managers. Identify gaps in technical understanding or change management, and design targeted leadership coaching.",
            "Implement Dynamic AI Resource Allocation: Establish a quarterly governance review to evaluate project returns. Shift budgets and team capacity rapidly away from underperforming pilots toward high-yield initiatives.",
            "Launch Advanced AI Specialisation Tracks: Select a cohort of 30-50 high-potential technical and business staff for expert-level training (e.g., LLM fine-tuning, advanced analytics) in partnership with a university or specialized institute."
        ],
        "month2": [
            "Formulate the Enterprise AI Ecosystem Strategy: Establish formal partnership frameworks with cloud providers, specialized startups, and academic research labs to secure early access to emerging models and top-tier talent.",
            "Embed Compliance-by-Design in Development Lifecycles: Create automated checklists and compliance gates (GDPR, ISO 42001, AI Act) directly in the development workspace, preventing code commits that violate standards.",
            "Launch an External AI Thought Leadership Campaign: Schedule executive speaking slots at key industry events, publish case studies on responsible AI practices, and participate in regulatory feedback groups."
        ],
        "month3": [
            "Publish the Annual Corporate AI Governance Report: Share a public transparency report showing details of the AI ethics program, model validation results, and community impact to build trust with customers, investors, and regulators.",
            "Deploy the Internal AI Talent Marketplace: Create a platform matching data scientists, engineers, and domain experts with active projects across different departments, optimizing talent utilization.",
            "Conduct an AI Value Architecture Review: Audit the financial models used to estimate AI value. Refine metrics to capture indirect benefits (e.g., employee retention, customer satisfaction) and align future budgets."
        ],
    },
    (8.5, 10.0): {
        "month1": [
            "Establish a C-Suite AI Succession and Development Plan: Create a career pipeline for technical leaders to transition into executive roles (e.g., Chief AI Officer). Include formal mentorship and board-level shadowing.",
            "Initiate Pre-Competitive AI Research Partnerships: Form a consortium with 2-3 research labs or universities to co-fund research in domain-specific AI models, securing exclusive rights to prototype outputs.",
            "Convene an Independent AI Ethics Board: Recruit external ethics experts, legal scholars, and representatives of impacted user groups. Formulate a charter granting the board veto power over high-risk AI deployments."
        ],
        "month2": [
            "Define AI-focused Mergers and Acquisitions (M&A) Criteria: Build an evaluation scorecard for assessing acquisition targets. Audit their data quality, model intellectual property, team talent, and compliance history.",
            "Launch the Global AI Employer Brand Campaign: Design a recruiting campaign positioning the organization as a premier destination for top-tier AI researchers. Highlight cutting-edge labs and ethical governance.",
            "Implement Predictive Risk Monitoring: Deploy advanced AI agents that scan industry news, academic papers, and regulatory updates to forecast compliance risks and model vulnerabilities before they affect operations."
        ],
        "month3": [
            "Contribute to Industry AI Standards and Benchmarks: Publish CISLF maturity insights and case studies to help define sector-wide benchmarks, collaborating with standards bodies (e.g., ISO, IEEE).",
            "Establish End-to-End AI Supply Chain Governance: Formally extend corporate ethical and security standards to all third-party model providers, APIs, and data brokers. Implement periodic compliance audits.",
            "Fund Breakthrough AI Transformation Bets: Allocate 20% of the AI budget to high-risk, high-reward initiatives that could disrupt the business model or open entirely new markets in the next 12-month cycle."
        ],
    },
}


# ---------------------------------------------------------------------------
# Industry-Specific Detailed Action Items (for the 90-day roadmap)
# ---------------------------------------------------------------------------
INDUSTRY_ROADMAP_ACTIONS: Dict[str, Dict[str, List[str]]] = {
    "IT services and service desk operations": {
        "month1": [
            "Conduct a service-value alignment audit on automated IT support bots to identify ticketing loop drop-offs and SLA breaches",
            "Establish user-centric frontline feedback channels to capture engineering and helpdesk staff complaints about AI tool friction"
        ],
        "month2": [
            "Standardise the human-in-the-loop escalation path for automated ticketing routing systems, ensuring complex SLA issues bypass bots",
            "Define service-desk value metrics (MTTR, first-contact resolution) specifically for AI-assisted operations"
        ],
        "month3": [
            "Deploy frontline dashboard displaying real-time AI assistance accuracy, SLA achievements, and user satisfaction trends",
            "Conduct a post-deployment audit of automated code-generation pilots to measure developer productivity vs code quality"
        ]
    },
    "Banking and financial services": {
        "month1": [
            "Initiate a comprehensive explainability audit on all credit risk scoring and credit underwriting AI models to ensure compliance with DORA",
            "Map all regulatory touchpoints (AML, fraud, compliance) to identify where AI tools require auditable decision paths"
        ],
        "month2": [
            "Establish mathematical fairness and bias monitoring boundaries for automated retail lending underwriting algorithms",
            "Formulate model-drift detection gates for algorithmic trading and automated investment models, linked to risk limits"
        ],
        "month3": [
            "Stand up the formal Model Risk Management (MRM) framework with independent validation pipelines and board reporting dashboards",
            "Conduct a simulation of regulatory audit inquiries on deep learning credit risk models to test team explanation capabilities"
        ]
    },
    "Healthcare and hospital administration": {
        "month1": [
            "Define clinical safety classification gates for diagnostic and clinical decision support AI tools, establishing formal risk tiers",
            "Review medical data access governance (patient privacy/HIPAA) for all research and operational AI model training sets"
        ],
        "month2": [
            "Establish patient data privacy safeguards with automated, tamper-proof audit logs for all clinical AI model inference queries",
            "Design nurse and clinician-led user-acceptance testing (UAT) to measure diagnostic alert utility and alert fatigue levels"
        ],
        "month3": [
            "Incorporate hospital board oversight protocols for clinical AI outcomes, linking models to institutional safety dashboards",
            "Roll out a mandatory training program for medical staff on AI diagnostic support limitations, emphasizing patient safety override rights"
        ]
    },
    "Manufacturing and plant operations": {
        "month1": [
            "Audit all predictive maintenance and automated quality control AI models against factory floor physical safety protocols",
            "Map operational data pipelines from IoT sensors to identify latency and data quality gaps affecting real-time model outputs"
        ],
        "month2": [
            "Deploy process integration gates linking predictive maintenance AI suggestions directly to maintenance crew workflow scheduling",
            "Launch training on physical human-machine interaction safety for plant operators working with AI-driven collaborative robots"
        ],
        "month3": [
            "Deploy plant-wide real-time dashboard tracking predictive model reliability, asset downtime reductions, and OEE improvements",
            "Perform a post-implementation review of raw material demand forecasting AI models to measure inventory turnover impact"
        ]
    },
    "Retail and e-commerce": {
        "month1": [
            "Audit customer touchpoint AI systems (recommendation engines, search algorithms, chat support) for loop friction and cart drop-offs",
            "Map data inputs for dynamic pricing and inventory forecasting models to verify customer data privacy compliance"
        ],
        "month2": [
            "Deploy stage-gate testing for dynamic pricing algorithms to prevent feedback loops, price spirals, and margin erosion",
            "Launch customer satisfaction (CSAT) and Net Promoter Score (NPS) feedback loops directly linked to AI recommendation outputs"
        ],
        "month3": [
            "Integrate customer experience metrics and conversion uplift values directly into the real-time marketing AI dashboard",
            "Run automated adversarial simulations on customer-facing generative AI chatbots to prevent prompt injections and offensive output"
        ]
    },
    "Education and learning services": {
        "month1": [
            "Draft a pedagogical AI alignment policy defining permissible boundaries of AI use for student grading and assessment support",
            "Initiate a faculty workload audit to measure time spent on administrative AI tools vs direct student engagement"
        ],
        "month2": [
            "Establish student data privacy controls and model governance guidelines for adaptive learning and personalized study bots",
            "Deliver professional development workshops for educators on detecting AI plagiarism and integrating AI as a teaching assistant"
        ],
        "month3": [
            "Implement institutional review protocols for student learning outcome metrics, comparing AI-supported vs traditional classrooms",
            "Establish student feedback channels to identify algorithmic bias or accessibility issues in personalized digital learning tools"
        ]
    },
    "Public services and citizen support": {
        "month1": [
            "Initiate a citizen data privacy and algorithmic fairness audit across all public assistance eligibility and benefit routing AI tools",
            "Establish public transparency guidelines detailing when and how AI is used in public service decision-making"
        ],
        "month2": [
            "Stand up a formal algorithmic bias advisory panel with community and academic representation to review high-risk public sector models",
            "Establish citizen grievance and review channels for appealing automated public service decisions"
        ],
        "month3": [
            "Publish the annual public sector AI governance registry detailing system accuracy, fairness metrics, and audit findings",
            "Deploy a public sector dashboard tracking service delivery turnaround times, citizen satisfaction, and AI accuracy metrics"
        ]
    },
    "Telecommunications": {
        "month1": [
            "Audit network optimization and automated traffic routing AI models for service delivery reliability and fallback recovery protocols",
            "Map customer data flow in dynamic billing and churn prediction models to identify privacy compliance risks"
        ],
        "month2": [
            "Deploy dynamic traffic load simulations to test AI network optimization resilience under sudden grid congestion events",
            "Define customer-centric service quality metrics (jitter, packet loss, network uptime) specifically for AI-managed nodes"
        ],
        "month3": [
            "Integrate dynamic network performance indicators and SLA achievement values directly into the real-time NOC dashboard",
            "Establish automated model-drift alert triggers for churn prediction algorithms to maintain retention campaign effectiveness"
        ]
    },
    "Logistics and transport": {
        "month1": [
            "Audit route optimization and automated dispatch algorithms against real-world driver safety and labor compliance standards",
            "Map physical data inputs from vehicle telematics to identify signal quality and latency gaps affecting delivery predictions"
        ],
        "month2": [
            "Deploy stage-gate testing for route planning AI models to prevent unsafe route suggestions and fleet-wide congestion loops",
            "Integrate dispatch crew feedback loops directly into the route planning model loop to capture localized traffic anomalies"
        ],
        "month3": [
            "Deploy a fleet-wide dashboard tracking real-time route efficiency, fuel consumption drops, and on-time delivery percentages",
            "Perform a post-implementation review of warehouse inventory positioning AI to measure space utilization improvements"
        ]
    },
    "Agriculture and rural services": {
        "month1": [
            "Audit yield prediction and precision irrigation AI models against localized soil sample historical records and weather sensors",
            "Map local cellular/IoT network connectivity gaps in rural areas affecting real-time sensor data transmission to AI systems"
        ],
        "month2": [
            "Deploy stage-gate testing for pesticide/fertilizer prescription AI models to prevent environmental run-offs and crop damage",
            "Conduct training workshops for field staff and farmers on interpreting AI recommendation outputs and manual override rights"
        ],
        "month3": [
            "Deploy a regional agriculture dashboard tracking water-use efficiency, crop health improvements, and dynamic yield predictions",
            "Conduct a cost-benefit analysis of AI-driven precision agriculture compared to traditional farming methodologies"
        ]
    },
    "Human resources and shared services": {
        "month1": [
            "Audit resume-screening and talent-matching AI algorithms for historical gender, racial, and educational background bias",
            "Map employee data usage across performance tracking and sentiment monitoring AI tools to verify internal privacy rules"
        ],
        "month2": [
            "Stand up an HR AI review committee to validate candidate sourcing models against employment equity standards",
            "Define employee-centric metrics (retention, internal promotion, talent acquisition time) for AI-supported recruiting"
        ],
        "month3": [
            "Publish an internal HR AI transparency charter outlining which systems use AI, how data is processed, and employee rights",
            "Establish feedback loops for hiring managers and candidates to report algorithmic anomalies or screening errors"
        ]
    },
    "Cybersecurity operations": {
        "month1": [
            "Audit security orchestration, automation, and response (SOAR) playbooks for vulnerability to prompt injection and data poisoning",
            "Map data flow of threat intelligence inputs to identify untrusted third-party feeds affecting threat detection models"
        ],
        "month2": [
            "Run MITRE ATLAS framework adversarial simulations to test the security stack's resilience against AI-driven cyber threats",
            "Establish baseline explainability requirements for AI security tools to help SOC analysts verify automated quarantine actions"
        ],
        "month3": [
            "Deploy automated integrity monitoring for security logs to prevent threat actors from tampering with AI training datasets",
            "Implement dynamic model retraining procedures for intrusion detection algorithms to counter adaptive hacker behaviors"
        ]
    }
}


# ---------------------------------------------------------------------------
# Risk Templates
# ---------------------------------------------------------------------------

RISK_POOL: List[Dict] = [
    {
        "name": "AI Talent Shortage and Retention",
        "probability": "High",
        "impact": "High",
        "description": (
            "Acute global shortage of qualified AI professionals creates delivery risk across the AI portfolio. "
            "Competition for top AI talent is intensifying, and organisations with immature AI cultures struggle to attract and retain the skills needed."
        ),
        "mitigation": (
            "Develop a comprehensive AI Talent Strategy covering build (upskilling existing employees), buy (targeted external recruitment), and borrow (strategic partnerships). "
            "Invest in AI employer brand and competitive total compensation benchmarking."
        ),
    },
    {
        "name": "Regulatory Non-Compliance Risk",
        "probability": "High",
        "impact": "High",
        "description": (
            "Rapidly evolving AI regulations — including the EU AI Act, GDPR, and sector-specific requirements — create material risk of non-compliance, "
            "with potential penalties, operational restrictions, and significant reputational damage."
        ),
        "mitigation": (
            "Appoint a dedicated AI Compliance Lead, commission a regulatory readiness assessment, and establish a continuous regulatory monitoring programme "
            "with proactive engagement with regulatory bodies to understand and shape requirements."
        ),
    },
    {
        "name": "AI Bias and Ethical Harm",
        "probability": "Medium",
        "impact": "High",
        "description": (
            "Deployment of AI systems without systematic bias detection and ethics governance creates risk of discriminatory outcomes, "
            "regulatory investigation, and lasting reputational damage that erodes customer and stakeholder trust."
        ),
        "mitigation": (
            "Implement mandatory bias assessment at every stage of the AI development lifecycle, adopt a formal AI Ethics Policy, "
            "and establish independent ethics review processes for all high-stakes AI systems before production deployment."
        ),
    },
    {
        "name": "Strategic Misalignment of AI Investments",
        "probability": "Medium",
        "impact": "Medium",
        "description": (
            "AI projects pursued without clear business outcome linkage risk delivering technical capability without business value, "
            "eroding executive confidence and future investment appetite for AI transformation."
        ),
        "mitigation": (
            "Implement AI portfolio governance requiring a formal business case and measurable KPIs as conditions for investment approval, "
            "with quarterly value realisation reviews and automatic review triggers if business KPIs are missed."
        ),
    },
    {
        "name": "Organisational Change Resistance",
        "probability": "Medium",
        "impact": "Medium",
        "description": (
            "Employee resistance to AI-driven change can undermine adoption rates, create productivity losses during transitions, "
            "and generate negative sentiment that hampers future AI initiatives and damages workplace trust."
        ),
        "mitigation": (
            "Deploy a structured AI Change Management methodology with transparent and repeated communication, a formal upskilling commitment, "
            "and active engagement with employee representative bodies and workforce councils for all major AI deployments."
        ),
    },
    {
        "name": "AI Model Performance Degradation",
        "probability": "Medium",
        "impact": "Medium",
        "description": (
            "AI models in production can experience silent performance drift due to data distribution shifts or concept drift, "
            "potentially delivering incorrect or harmful outputs without detection or alert."
        ),
        "mitigation": (
            "Implement automated model monitoring with performance alerting, establish formal model retraining and revalidation protocols, "
            "and conduct regular business-led model performance reviews to ensure continued fitness for purpose."
        ),
    },
    {
        "name": "AI Vendor Concentration Risk",
        "probability": "Low",
        "impact": "Medium",
        "description": (
            "Over-reliance on a small number of AI platform and model providers creates concentration risk, "
            "potential for commercial lock-in, and strategic vulnerability if providers change pricing, capabilities, or availability."
        ),
        "mitigation": (
            "Develop a multi-vendor AI platform strategy with portability standards embedded in all AI procurement contracts, "
            "and maintain sufficient internal capability to evaluate, migrate, or switch between AI platforms as needed."
        ),
    },
    {
        "name": "Data Quality and Governance Deficits",
        "probability": "Medium",
        "impact": "High",
        "description": (
            "AI model performance is fundamentally constrained by the quality, availability, and governance of training and operational data. "
            "Poor data quality silently undermines AI investment value and creates compounding downstream risks."
        ),
        "mitigation": (
            "Invest in enterprise data governance infrastructure, implement data quality standards specific to AI use cases, "
            "and establish data product ownership with clear business accountability for AI data assets."
        ),
    },
]


def _select_three_risks(overall_score: float) -> List[Dict]:
    """Select three contextually appropriate risks based on the overall maturity score."""
    if overall_score < 4.0:
        indices = [0, 1, 2]      # High-High-High (talent, regulatory, bias)
    elif overall_score < 5.5:
        indices = [1, 2, 3]      # Regulatory, bias, strategic misalignment
    elif overall_score < 7.0:
        indices = [3, 4, 5]      # Misalignment, change resistance, model drift
    elif overall_score < 8.5:
        indices = [4, 5, 6]      # Change resistance, model drift, vendor concentration
    else:
        indices = [5, 6, 7]      # Model drift, vendor concentration, data governance
    return [RISK_POOL[i] for i in indices]


# ---------------------------------------------------------------------------
# Priority Action Selection
# ---------------------------------------------------------------------------

PRIORITY_ACTIONS: Dict[int, List[Tuple[str, int, str]]] = {
    # pillar_num: [(action_title, pillar_ref, timeline), ...]
    1: [
        ("Appoint or empower a dedicated AI executive leader with formal mandate", 1, "30 days"),
        ("Commission executive AI vision and strategy workshop", 1, "30 days"),
        ("Launch executive AI literacy development programme", 1, "60 days"),
        ("Establish AI as standing board agenda item", 1, "30 days"),
        ("Publish organisation-wide AI vision and transformation roadmap", 1, "60 days"),
    ],
    2: [
        ("Implement AI portfolio governance with mandatory business KPI requirements", 2, "45 days"),
        ("Establish cross-functional AI Steering Committee with shared accountability", 2, "30 days"),
        ("Develop and launch AI ROI measurement and benefits tracking framework", 2, "60 days"),
        ("Co-develop technology roadmap with business leadership for AI alignment", 2, "90 days"),
        ("Deploy real-time AI portfolio performance executive dashboard", 2, "90 days"),
    ],
    3: [
        ("Establish AI Centre of Excellence with funding and delivery mandate", 3, "30 days"),
        ("Launch organisation-wide AI literacy and upskilling programme", 3, "45 days"),
        ("Implement structured AI change management for all new AI deployments", 3, "60 days"),
        ("Create ring-fenced AI experimentation fund with fast-fail methodology", 3, "45 days"),
        ("Deploy AI Skills Framework with career pathways for all functions", 3, "90 days"),
    ],
    4: [
        ("Formally adopt and publish AI Ethics Policy at board level", 4, "45 days"),
        ("Implement mandatory AI bias assessment in the development lifecycle", 4, "60 days"),
        ("Establish board-level AI risk oversight structure with named accountability", 4, "30 days"),
        ("Commission AI regulatory compliance assessment and roadmap", 4, "30 days"),
        ("Deploy automated AI governance monitoring for production systems", 4, "90 days"),
    ],
}


def _select_priority_actions(pillar_scores: Dict[int, float]) -> List[Tuple[str, int, str]]:
    """
    Select the top 5 priority actions by surfacing the weakest pillar actions first.

    Pillars are sorted ascending by score so the lowest-scoring (highest-priority)
    pillars contribute actions first.
    """
    sorted_pillars = sorted(pillar_scores.items(), key=lambda x: x[1])
    selected: List[Tuple[str, int, str]] = []
    pillar_index: Dict[int, int] = {p: 0 for p in range(1, 5)}

    while len(selected) < 5:
        progress = False
        for pillar_num, _ in sorted_pillars:
            if len(selected) >= 5:
                break
            idx = pillar_index[pillar_num]
            actions = PRIORITY_ACTIONS[pillar_num]
            if idx < len(actions):
                selected.append(actions[idx])
                pillar_index[pillar_num] += 1
                progress = True
        if not progress:
            break

    return selected[:5]


# ---------------------------------------------------------------------------
# Executive Summary & Readiness Justification
# ---------------------------------------------------------------------------

def _executive_summary(
    overall_score: float,
    pillar_scores: Dict[int, float],
    role: str,
    industry: str,
) -> str:
    strongest = max(pillar_scores, key=pillar_scores.get)
    weakest   = min(pillar_scores, key=pillar_scores.get)
    p_names = {
        1: "Leadership Mindset & Vision",
        2: "Strategic Business-Technology Alignment",
        3: "Organisational Capability & Culture",
        4: "Responsible AI Governance",
    }
    status = get_maturity_label(overall_score)
    return (
        f"This CISLF Framework Assessment evaluates the AI transformation readiness of a "
        f"{industry} organisation, conducted from the perspective of its {role}. "
        f"Based on the structured 20-question assessment across all four CISLF pillars, "
        f"the organisation achieves an overall maturity score of {overall_score}/10, "
        f"classified as '{status}'. "
        f"'{p_names[strongest]}' (Score: {pillar_scores[strongest]}/10) represents the "
        f"strongest organisational pillar — a foundation to leverage and protect. "
        f"'{p_names[weakest]}' (Score: {pillar_scores[weakest]}/10) represents the most "
        f"critical development priority, requiring the immediate allocation of leadership "
        f"attention and resources. The 90-day action plan and pillar recommendations below "
        f"provide a structured, evidence-based pathway to accelerate AI transformation "
        f"maturity across all four dimensions of the CISLF framework."
    )


def _readiness_justification(
    overall_score: float, pillar_scores: Dict[int, float]
) -> str:
    p = pillar_scores
    return (
        f"Score reflects weighted assessment across all four CISLF pillars — "
        f"Leadership & Vision: {p[1]}/10, Strategic Alignment: {p[2]}/10, "
        f"Capability & Culture: {p[3]}/10, Responsible Governance: {p[4]}/10 — "
        f"normalised to reflect the balanced importance of all pillars for sustained AI transformation success."
    )


# ---------------------------------------------------------------------------
# Main Report Builder
# ---------------------------------------------------------------------------

def build_manual_report(
    answers: Dict[str, int],
    role: str = "Technology Executive",
    industry: str = "Not specified",
) -> str:
    """
    Generate a complete, formatted CISLF Strategic Analysis Report
    using the rule-based scoring and template engine.

    Args:
        answers:  Dict mapping question_id → selected rating (1-5).
        role:     Executive role string.
        industry: Industry/sector string.

    Returns:
        Full CISLF report formatted as a plain-text string.
    """
    role     = role.strip()     or "Technology Executive"
    industry = industry.strip() or "Not specified"

    # ── 1. Calculate scores ───────────────────────────────────────────────
    pillar_scores, overall_score, breakdown = calculate_all_scores(answers, industry=industry)

    # ── 2. Select templates ───────────────────────────────────────────────
    def get(template: dict, pillar: int, score: float):
        return template[pillar][get_band(score)]

    overall_band  = get_band(overall_score)
    # Deep copy to allow modifying lists without affecting global template
    action_plan   = copy.deepcopy(ACTION_PLAN_TEXTS[overall_band])
    
    # Append industry-specific detailed action items if available
    if industry in INDUSTRY_ROADMAP_ACTIONS:
        ind_actions = INDUSTRY_ROADMAP_ACTIONS[industry]
        action_plan["month1"].extend(ind_actions["month1"])
        action_plan["month2"].extend(ind_actions["month2"])
        action_plan["month3"].extend(ind_actions["month3"])
    risks         = _select_three_risks(overall_score)
    p_actions     = _select_priority_actions(pillar_scores)

    # ── 3. Build report lines ─────────────────────────────────────────────
    L: List[str] = []

    def line(s: str = "") -> None:
        L.append(s)

    # Header
    line("## 📄 CISLF STRATEGIC ANALYSIS REPORT")
    line(f"**Prepared for:** {role} | {industry}")
    line()
    line("**Framework:** Comprehensive Intelligent Strategic Leadership Framework (CISLF)")
    line("**Author:** Mohammad Quasif, DBA | Kennedy University of Baptist, France")
    line("**Assessment Method:** CISLF Rule-Based Framework Questionnaire (20 Questions)")
    line("---")
    line()

    # Executive Summary
    line("## EXECUTIVE SUMMARY")
    line(_executive_summary(overall_score, pillar_scores, role, industry))
    line()

    # Readiness Score
    line(f"### TRANSFORMATION READINESS SCORE: {overall_score}/10")
    line(_readiness_justification(overall_score, pillar_scores))
    line()
    line("---")
    line()

    # ── Score Methodology (industry-aware) ───────────────────────────────────
    if industry in INDUSTRY_SCORING_CONFIG:
        cfg = INDUSTRY_SCORING_CONFIG[industry]
        line("## ⚙️ SCORING METHODOLOGY")
        line(f"**Industry Context:** {industry}")
        line()
        line(f"*{breakdown['score_note']}*")
        line()
        line("**Pillar Weight Configuration (Industry-Adjusted):**")
        p_names_short = {
            1: "Leadership & Vision", 2: "Strategic Alignment",
            3: "Capability & Culture", 4: "Responsible Governance"
        }
        pw = breakdown['pillar_weights']
        total_w = breakdown['total_weight']
        for p_num in range(1, 5):
            w = pw.get(p_num, 1.0)
            pct = int(round((w / total_w) * 100))
            bar = '█' * pct + '░' * (100 - pct)
            line(f"- Pillar {p_num} ({p_names_short[p_num]}): Weight {w}× → {pct}% of overall score")
        line()
        if breakdown['triggered_caps']:
            line("**⚠️ Critical Question Penalties Applied:**")
            for cap in breakdown['triggered_caps']:
                line(f"- {cap}")
            line()
        if breakdown['applied_synergy']:
            line("**✅ Pillar Synergy Bonuses Applied (+0.3 each):**")
            for syn in breakdown['applied_synergy']:
                line(f"- {syn}")
            line()
        line(f"**Base Pillar Scores (pre-synergy):** " +
             " | ".join(f"P{p}: {breakdown['base_scores'][p]}/10" for p in range(1, 5)))
        line(f"**Final Pillar Scores (post-synergy):** " +
             " | ".join(f"P{p}: {breakdown['final_scores'][p]}/10" for p in range(1, 5)))
        line()
        line(f"**Industry-Weighted Overall Score:** {overall_score}/10")
        line()
        line("---")
        line()

    # Industry Specific Analysis
    if industry in INDUSTRY_RULES:
        rules = INDUSTRY_RULES[industry]
        line("## 🏭 INDUSTRY-SPECIFIC ANALYSIS")
        line(f"**Sector:** {industry}")
        line()
        line(f"**TYPICAL LEADERSHIP RISK:**")
        line(f"- {rules['risk']}")
        line()
        line(f"**CISLF EMPHASIS & MITIGATION:**")
        line(f"- {rules['emphasis']}")
        line()
        line("> *This industry-specific lens should be applied when evaluating the pillar scores below.*")
        line()

    # ── Four Pillars ──────────────────────────────────────────────────────
    icons = {1: "🧠", 2: "🔗", 3: "🏗️", 4: "⚖️"}
    for p_num in range(1, 5):
        score  = pillar_scores[p_num]
        p_data = PILLAR_QUESTIONS[p_num]
        icon = icons.get(p_num, "")

        line(f"## {icon} PILLAR {p_num}: {p_data['title'].upper()}")
        line()
        line("**ASSESSMENT:**")
        line(get(ASSESSMENT_TEXTS, p_num, score))
        line()
        line("**✅ STRENGTHS IDENTIFIED:**")
        for s in get(STRENGTH_TEXTS, p_num, score):
            line(f"- {s}")
        line()
        line("**⚠️ CRITICAL GAPS:**")
        for g in get(GAP_TEXTS, p_num, score):
            line(f"- {g}")
        line()
        line("**💡 STRATEGIC RECOMMENDATIONS:**")
        for r in get(RECOMMENDATION_TEXTS, p_num, score):
            line(f"- {r}")
        line()
        line(f"**PILLAR SCORE:** {score}/10")
        line()
        line("---")
        line()

    # ── 90-Day Action Plan ─────────────────────────────────────────────────
    line("## 📅 90-DAY ACTION PLAN")
    line()
    line("### 🚀 MONTH 1 — FOUNDATION (Days 1-30):")
    for a in action_plan["month1"]:
        line(f"- {a}")
    line()
    line("### ⚡ MONTH 2 — ACCELERATION (Days 31-60):")
    for a in action_plan["month2"]:
        line(f"- {a}")
    line()
    line("### 🔄 MONTH 3 — INTEGRATION (Days 61-90):")
    for a in action_plan["month3"]:
        line(f"- {a}")
    line()
    line("---")
    line()

    # ── Risk Assessment ────────────────────────────────────────────────────
    line("## 🛑 RISK ASSESSMENT")
    line()
    for i, risk in enumerate(risks, 1):
        line(f"### RISK {i}: {risk['name']}")
        line(f"- **Probability:** {risk['probability']} | **Impact:** {risk['impact']}")
        line(f"- **Description:** {risk['description']}")
        line(f"- **Mitigation:** {risk['mitigation']}")
        line()
    line("---")
    line()

    # ── Priority Actions ────────────────────────────────────────────────────
    line("## 🏆 TOP 5 PRIORITY ACTIONS")
    line()
    for i, (action, p_ref, timeline) in enumerate(p_actions, 1):
        line(f"**{i}. {action}** | Pillar {p_ref} | {timeline}")
        line(f"*Prioritised from CISLF pillar score analysis — targeting the highest-leverage gaps first.*")
        line()
    line("---")
    line()

    # ── Maturity Scorecard ─────────────────────────────────────────────────
    line("## 📈 CISLF MATURITY SCORECARD")
    line()

    scorecard_rows = [
        ("Pillar 1 — Leadership Mindset & Vision", 1),
        ("Pillar 2 — Strategic Business-Tech Alignment", 2),
        ("Pillar 3 — Organisational Capability & Culture", 3),
        ("Pillar 4 — Responsible AI Governance", 4),
    ]
    for label, p_num in scorecard_rows:
        s      = pillar_scores[p_num]
        status = get_maturity_label(s)
        line(f"- **{label}:** {s}/10  |  *{status}*")

    line()
    line(f"### OVERALL CISLF MATURITY SCORE: {overall_score}/10")
    line(f"**Status:** {get_maturity_label(overall_score)}")
    line()
    line("---")
    line()

    # ── Framework Reference ────────────────────────────────────────────────
    line("## 📚 FRAMEWORK REFERENCE")
    line(
        "> This analysis is powered by the CISLF Framework — Quasif, M. (2025). Strategic "
        "Leadership for AI-Driven Business Transformation: A Cross-Industry Framework for "
        "Technology Executives. DBA Thesis. Kennedy University of Baptist, France."
    )
    line()
    line("*Assessment Method: Rule-Based CISLF Framework Questionnaire (No AI required)*")
    line()
    line("END OF REPORT")

    return "\n".join(L)
