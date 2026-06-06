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

CISLF Framework — Comprehensive Intelligent Strategic Leadership Framework
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
# Industry Specific Rules
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
# Questionnaire Definition
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


def get_dynamic_questions(industry: str) -> Dict[int, dict]:
    """Dynamically tailor the 20 CISLF questions to the selected industry."""
    questions = copy.deepcopy(PILLAR_QUESTIONS)
    
    if industry == "Not specified" or industry not in INDUSTRY_RULES:
        return questions
        
    rules = INDUSTRY_RULES[industry]
    risk_text = rules["risk"].lower().rstrip('.')
    emphasis_text = rules["emphasis"].lower().rstrip('.')
    ind_name = industry.split(" and ")[0]
    
    # Pillar 1 (Mindset)
    questions[1]["questions"][0]["text"] += f" (Specifically addressing the sector risk that {risk_text})"
    questions[1]["questions"][3]["text"] += f" (Including literacy on {ind_name} specific AI applications)"
    
    # Pillar 2 (Alignment)
    questions[2]["questions"][0]["text"] += f" (Particularly metrics tracking {emphasis_text})"
    questions[2]["questions"][2]["text"] += f" (Ensuring cross-functional {emphasis_text})"
    
    # Pillar 3 (Capability)
    questions[3]["questions"][1]["text"] += f" (Tailored for {ind_name} operational workflows)"
    questions[3]["questions"][3]["text"] += f" (Empowering frontline {ind_name} staff)"
    
    # Pillar 4 (Governance)
    questions[4]["questions"][0]["text"] += f" (Addressing {ind_name} specific regulatory risks)"
    questions[4]["questions"][1]["text"] += f" (To prevent harms such as {risk_text})"
    
    return questions

# ---------------------------------------------------------------------------
# Score Calculation
# ---------------------------------------------------------------------------

def calculate_pillar_score(pillar_num: int, answers: Dict[str, int]) -> float:
    """
    Calculate the weighted, normalised score (0–10) for a single CISLF pillar.

    Formula:
        raw = sum(answer_value[i] * weight[i])   for all questions in pillar
        max_raw = sum(5 * weight[i])             (max possible raw score)
        score = (raw / max_raw) * 10

    Args:
        pillar_num: 1 to 4.
        answers:    Dict mapping question_id → selected rating (1-5).

    Returns:
        Float score in range [0.0, 10.0], rounded to 1 decimal place.
    """
    questions = PILLAR_QUESTIONS[pillar_num]["questions"]
    total_weighted = 0.0
    total_weight = 0.0

    for q in questions:
        qid = q["id"]
        weight = q["weight"]
        # Default to 1 (lowest) if question not answered
        value = float(answers.get(qid, 1))
        total_weighted += value * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    max_possible = 5.0 * total_weight
    score = (total_weighted / max_possible) * 10.0
    return round(min(score, 10.0), 1)


def calculate_all_scores(answers: Dict[str, int]) -> Tuple[Dict[int, float], float]:
    """
    Calculate scores for all four pillars and the overall CISLF score.

    Args:
        answers: Dict mapping question_id → rating (1-5).

    Returns:
        Tuple of (pillar_scores_dict, overall_score).
        pillar_scores_dict: {1: float, 2: float, 3: float, 4: float}
        overall_score: average of all four pillar scores.
    """
    pillar_scores = {p: calculate_pillar_score(p, answers) for p in range(1, 5)}
    overall = round(sum(pillar_scores.values()) / 4, 1)
    return pillar_scores, overall


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
            "Establish an Emergency AI Governance Task Force with CEO sponsorship — conduct a rapid risk triage across all live AI systems and define immediate mitigation actions",
            "Commission a comprehensive CISLF AI Maturity Assessment with an external advisory firm to baseline the current state and prioritise remediation across all four pillars",
            "Pause all AI projects lacking a defined business owner and measurable outcomes — set a 30-day deadline for projects to be resubmitted with governance-compliant business cases",
        ],
        "month2": [
            "Launch an intensive Executive AI Literacy Sprint — a 4-week facilitated programme for all C-suite and senior leaders, culminating in a published AI vision statement",
            "Publish a draft AI Ethics Policy and AI Investment Framework for stakeholder review, with board sign-off targeted for Month 3",
            "Launch an AI Upskilling Pilot with 200–500 employees across diverse roles and functions to build evidence and momentum for the scaled programme",
        ],
        "month3": [
            "Formally adopt the AI Ethics Policy and AI Investment Framework at board level — communicate publicly and embed in all project governance processes",
            "Establish the AI Centre of Excellence with founding team, mandate, and 12-month delivery plan approved at executive level",
            "Re-launch the reprioritised AI portfolio with complete business cases, defined KPIs, governance controls, and named executive sponsors for every initiative",
        ],
    },
    (4.0, 5.4): {
        "month1": [
            "Conduct a Strategic AI Gap Analysis — map all current AI initiatives against strategic business objectives and identify misalignment, duplication, and investment gaps",
            "Facilitate a Leadership AI Vision Workshop — produce a board-endorsed AI transformation vision statement and 3-year strategic roadmap within 30 days",
            "Design a comprehensive AI Skills Framework and structured upskilling programme targeting all workforce segments, with board funding approval by month end",
        ],
        "month2": [
            "Launch AI Portfolio Governance — implement the stage-gate investment process and mandatory business KPI requirements for all AI projects above agreed thresholds",
            "Stand up cross-functional delivery squads for the top 3 strategic AI priorities with co-named business and technology owners and defined success metrics",
            "Roll out AI literacy training to 100% of management — all managers complete the foundational AI programme by end of Month 2",
        ],
        "month3": [
            "Formalise the AI Governance Framework — AI Ethics Policy, bias review process, and board AI risk reporting all operational and embedded in project governance",
            "Launch the AI Centre of Excellence with a defined business engagement model, service catalogue, and operating budget approved by the executive",
            "Publish the AI Transformation Roadmap — 3-year commitments, milestone calendar, and resource plan communicated to all employees via CEO town hall",
        ],
    },
    (5.5, 6.9): {
        "month1": [
            "Embed AI agenda items as standing items in all executive and board meetings and update the strategic plan to explicitly reference AI transformation milestones",
            "Mature the AI portfolio governance process — implement real-time dashboard for investment performance and business KPI tracking available to all executive sponsors",
            "Scale the upskilling programme to 50% of total workforce coverage, with role-specific pathways launched for the top 5 business functions",
        ],
        "month2": [
            "Launch the federated AI CoE model — embed dedicated AI Practitioners into each major business unit alongside the central CoE hub to build distributed capability",
            "Implement mandatory AI bias testing as a non-negotiable development lifecycle gate for all new AI systems being developed or procured",
            "Establish monthly cross-functional AI Outcomes Reviews — joint business and technology sessions reviewing adoption, value delivery, and strategic alignment",
        ],
        "month3": [
            "Deploy automated AI governance monitoring tools for bias, performance drift, and compliance alerting in all AI systems operating in production",
            "Launch the AI Innovation Programme — a structured experimentation process with ringfenced budget, fast-fail governance, and quarterly showcase events",
            "Publish an internal AI Maturity Progress Report — a transparent scorecard communicating transformation progress and next priorities to all employees",
        ],
    },
    (7.0, 8.4): {
        "month1": [
            "Conduct an AI Leadership Excellence Review — assess AI leadership capability across the senior management population and define targeted development priorities",
            "Implement Dynamic AI Portfolio Rebalancing — establish a formal quarterly process for rapid resource redeployment based on strategic performance and market signals",
            "Launch Advanced AI Specialisation Tracks — develop expert-level AI capability in 30–50 high-potential employees through partnership with a leading university or research institute",
        ],
        "month2": [
            "Define and launch an AI Ecosystem Strategy — formalise engagement models with AI platform vendors, research startups, and academic partners to maintain an innovation edge",
            "Embed Privacy-by-Design and Governance-by-Design standards in all AI development processes, with automated compliance checks integrated into the DevOps pipeline",
            "Launch an External AI Thought Leadership Programme — publish 2–3 articles or white papers, secure conference speaking slots, and initiate regulatory working group participation",
        ],
        "month3": [
            "Publish the first annual AI Governance Transparency Report — demonstrating responsible AI practices to external stakeholders, regulators, customers, and investors",
            "Launch the AI Talent Marketplace — a formal internal platform to optimise the deployment and development of advanced AI skills across the strategic portfolio",
            "Commission an AI Value Architecture Review — comprehensively quantify the full portfolio AI value and optimise investment allocation for maximum strategic return",
        ],
    },
    (8.5, 10.0): {
        "month1": [
            "Commission a formal AI Leadership Succession Plan — identify, assess, and begin developing the next cohort of AI leaders through a structured 18-month programme",
            "Launch AI Ecosystem Innovation Partnerships — co-development agreements with 2–3 leading AI research institutions for pre-competitive capability building",
            "Establish an independent AI Ethics Advisory Board — recruit external domain experts, civil society representatives, and issue first annual terms of reference",
        ],
        "month2": [
            "Develop AI M&A Evaluation Criteria — a formal framework for assessing acquisition targets on AI capability fit, data assets, talent quality, and governance maturity",
            "Launch the AI Talent Brand Initiative — an external marketing campaign and employer recognition strategy to attract world-class AI professionals at all levels",
            "Implement Predictive AI Governance Intelligence — automated early warning capability for emerging compliance risks before they become regulatory or reputational issues",
        ],
        "month3": [
            "Publish an industry AI Leadership Benchmark — contribute CISLF maturity insights to an industry body, academic journal, or regulatory consultation to define sector best practice",
            "Implement AI Ecosystem Governance — formally extend responsible AI standards, audit rights, and compliance expectations to all major AI vendors and technology partners",
            "Launch the AI Value Amplification Programme — identify and fund 5 breakthrough AI opportunities for focused investment in the next 12-month strategic cycle",
        ],
    },
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
    pillar_scores, overall_score = calculate_all_scores(answers)

    # ── 2. Select templates ───────────────────────────────────────────────
    def get(template: dict, pillar: int, score: float):
        return template[pillar][get_band(score)]

    overall_band  = get_band(overall_score)
    action_plan   = ACTION_PLAN_TEXTS[overall_band]
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
    line("**Framework:** CISLF — Comprehensive Intelligent Strategic Leadership Framework")
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
