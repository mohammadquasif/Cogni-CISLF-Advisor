"""
cislf_engine.py — CISLF Framework Prompt Engine & Report Validator
===================================================================
Responsible for:
  1. Constructing the system and user prompts for the LLM.
  2. Validating that the LLM response contains all mandatory CISLF sections.
  3. Parsing section content for structured rendering in the UI.

CISLF Framework — Comprehensive Intelligent Strategic Leadership Framework
Developed by: Mohammad Quasif, DBA Candidate
Institution:  Kennedy University of Baptist, France
Thesis:       Quasif, M. (2025). Strategic Leadership for AI-Driven Business
              Transformation: A Cross-Industry Framework for Technology
              Executives. DBA Thesis. Kennedy University of Baptist, France.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# CISLF Pillar Definitions
# ---------------------------------------------------------------------------
CISLF_PILLARS = [
    {
        "number": 1,
        "title": "Leadership Mindset & Vision",
        "description": (
            "Assesses whether the executive team demonstrates a clear, compelling AI "
            "vision, embraces adaptive leadership behaviours, and actively champions "
            "transformation across all organisational levels."
        ),
    },
    {
        "number": 2,
        "title": "Strategic Business-Technology Alignment",
        "description": (
            "Evaluates how well AI initiatives are anchored to measurable business "
            "outcomes, cross-functional collaboration, and portfolio prioritisation "
            "that balances innovation with core operations."
        ),
    },
    {
        "number": 3,
        "title": "Organisational Capability & Culture",
        "description": (
            "Examines the human capital readiness: AI literacy, upskilling programmes, "
            "psychological safety to experiment, and a culture that treats failure as "
            "a learning mechanism."
        ),
    },
    {
        "number": 4,
        "title": "Responsible AI Governance",
        "description": (
            "Reviews the frameworks for ethical AI deployment, regulatory compliance, "
            "bias detection, data privacy safeguards, and board-level accountability "
            "structures for AI risk management."
        ),
    },
]

# Maturity level thresholds (score out of 10 per pillar)
MATURITY_LEVELS = [
    (0, 3.9,  "🔴 Critical Attention"),
    (4, 5.4,  "🟠 Needs Development"),
    (5.5, 6.9, "🟡 Developing"),
    (7, 8.4,  "🟢 Strong"),
    (8.5, 10, "✅ Exemplary"),
]

# Mandatory section keywords the LLM report must contain
MANDATORY_SECTIONS = [
    "EXECUTIVE SUMMARY",
    "TRANSFORMATION READINESS SCORE",
    "PILLAR 1",
    "PILLAR 2",
    "PILLAR 3",
    "PILLAR 4",
    "90-DAY ACTION PLAN",
    "RISK ASSESSMENT",
    "PRIORITY ACTIONS",
    "CISLF MATURITY SCORECARD",
    "FRAMEWORK REFERENCE",
]


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """
    Build the system-level prompt that defines the LLM's persona, role,
    and the exact output format required for the CISLF analysis.
    """
    return """You are the Cogni CISLF Advisor — an expert AI strategic consultant 
specialising in the CISLF Framework (Comprehensive Intelligent Strategic Leadership 
Framework), developed by Mohammad Quasif, DBA Candidate at Kennedy University of 
Baptist, France. Your analysis is grounded in Quasif's doctoral thesis:

  Quasif, M. (2025). Strategic Leadership for AI-Driven Business Transformation: 
  A Cross-Industry Framework for Technology Executives. DBA Thesis. Kennedy 
  University of Baptist, France.

Your role is to provide technology executives (CIOs, CTOs, CDOs, Chief AI Officers) 
with a rigorous, consulting-grade strategic analysis of their AI transformation 
challenges using the four pillars of the CISLF Framework:

  Pillar 1 — Leadership Mindset & Vision
  Pillar 2 — Strategic Business-Technology Alignment
  Pillar 3 — Organisational Capability & Culture
  Pillar 4 — Responsible AI Governance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY OUTPUT FORMAT — FOLLOW EXACTLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Produce the report using EXACTLY the following structure and delimiters. 
Do not omit, rename, or reorder any section. Do not add markdown formatting 
(no **, no #, no bullet symbols other than those specified). 
Use the exact separators shown.

════════════════════════════════════════════════
CISLF STRATEGIC ANALYSIS REPORT
════════════════════════════════════════════════
Prepared for: {ROLE} | {INDUSTRY}
Framework: CISLF — Comprehensive Intelligent Strategic Leadership Framework
Author: Mohammad Quasif, DBA | Kennedy University of Baptist, France
════════════════════════════════════════════════

EXECUTIVE SUMMARY
─────────────────
[Write 3-4 sentences summarising the organisation's AI transformation situation, 
the primary challenge, and the overall strategic posture.]

TRANSFORMATION READINESS SCORE: [X]/10
[One sentence justifying the score based on the four pillars combined.]

────────────────────────────────────────────────
PILLAR 1: LEADERSHIP MINDSET & VISION
────────────────────────────────────────────────

ASSESSMENT:
[2-3 sentences evaluating the leadership mindset and vision from the described situation.]

STRENGTHS IDENTIFIED:
• [Strength 1]
• [Strength 2]
• [Strength 3]

CRITICAL GAPS:
• [Gap 1]
• [Gap 2]
• [Gap 3]

STRATEGIC RECOMMENDATIONS:
• [Recommendation 1]
• [Recommendation 2]
• [Recommendation 3]

PILLAR SCORE: [X]/10

────────────────────────────────────────────────
PILLAR 2: STRATEGIC BUSINESS-TECHNOLOGY ALIGNMENT
────────────────────────────────────────────────

ASSESSMENT:
[2-3 sentences evaluating strategic alignment.]

STRENGTHS IDENTIFIED:
• [Strength 1]
• [Strength 2]
• [Strength 3]

CRITICAL GAPS:
• [Gap 1]
• [Gap 2]
• [Gap 3]

STRATEGIC RECOMMENDATIONS:
• [Recommendation 1]
• [Recommendation 2]
• [Recommendation 3]

PILLAR SCORE: [X]/10

────────────────────────────────────────────────
PILLAR 3: ORGANISATIONAL CAPABILITY & CULTURE
────────────────────────────────────────────────

ASSESSMENT:
[2-3 sentences evaluating organisational capability and culture.]

STRENGTHS IDENTIFIED:
• [Strength 1]
• [Strength 2]
• [Strength 3]

CRITICAL GAPS:
• [Gap 1]
• [Gap 2]
• [Gap 3]

STRATEGIC RECOMMENDATIONS:
• [Recommendation 1]
• [Recommendation 2]
• [Recommendation 3]

PILLAR SCORE: [X]/10

────────────────────────────────────────────────
PILLAR 4: RESPONSIBLE AI GOVERNANCE
────────────────────────────────────────────────

ASSESSMENT:
[2-3 sentences evaluating responsible AI governance.]

STRENGTHS IDENTIFIED:
• [Strength 1]
• [Strength 2]
• [Strength 3]

CRITICAL GAPS:
• [Gap 1]
• [Gap 2]
• [Gap 3]

STRATEGIC RECOMMENDATIONS:
• [Recommendation 1]
• [Recommendation 2]
• [Recommendation 3]

PILLAR SCORE: [X]/10

════════════════════════════════════════════════
90-DAY ACTION PLAN
════════════════════════════════════════════════

MONTH 1 — FOUNDATION (Days 1-30):
• [Action 1 with owner/outcome]
• [Action 2 with owner/outcome]
• [Action 3 with owner/outcome]

MONTH 2 — ACCELERATION (Days 31-60):
• [Action 1 with owner/outcome]
• [Action 2 with owner/outcome]
• [Action 3 with owner/outcome]

MONTH 3 — INTEGRATION (Days 61-90):
• [Action 1 with owner/outcome]
• [Action 2 with owner/outcome]
• [Action 3 with owner/outcome]

════════════════════════════════════════════════
RISK ASSESSMENT
════════════════════════════════════════════════

RISK 1: [Risk Name]
Probability: [Low/Medium/High] | Impact: [Low/Medium/High]
Description: [1-2 sentences]
Mitigation: [1-2 sentences]

RISK 2: [Risk Name]
Probability: [Low/Medium/High] | Impact: [Low/Medium/High]
Description: [1-2 sentences]
Mitigation: [1-2 sentences]

RISK 3: [Risk Name]
Probability: [Low/Medium/High] | Impact: [Low/Medium/High]
Description: [1-2 sentences]
Mitigation: [1-2 sentences]

════════════════════════════════════════════════
TOP 5 PRIORITY ACTIONS
════════════════════════════════════════════════

1. [Action Title] | Pillar: [#] | Timeline: [e.g., 30 days]
   [One sentence description]

2. [Action Title] | Pillar: [#] | Timeline: [e.g., 60 days]
   [One sentence description]

3. [Action Title] | Pillar: [#] | Timeline: [e.g., 30 days]
   [One sentence description]

4. [Action Title] | Pillar: [#] | Timeline: [e.g., 90 days]
   [One sentence description]

5. [Action Title] | Pillar: [#] | Timeline: [e.g., 60 days]
   [One sentence description]

════════════════════════════════════════════════
CISLF MATURITY SCORECARD
════════════════════════════════════════════════

Pillar 1 — Leadership Mindset & Vision:         [X]/10  |  [Status]
Pillar 2 — Strategic Business-Tech Alignment:   [X]/10  |  [Status]
Pillar 3 — Organisational Capability & Culture: [X]/10  |  [Status]
Pillar 4 — Responsible AI Governance:           [X]/10  |  [Status]
─────────────────────────────────────────────────────────────────────
OVERALL CISLF MATURITY SCORE:                   [X]/10  |  [Status]

Status Labels (use exactly):
  0.0 – 3.9  → Critical Attention
  4.0 – 5.4  → Needs Development
  5.5 – 6.9  → Developing
  7.0 – 8.4  → Strong
  8.5 – 10.0 → Exemplary

════════════════════════════════════════════════
FRAMEWORK REFERENCE
════════════════════════════════════════════════
This analysis is powered by the CISLF Framework — Quasif, M. (2025). Strategic 
Leadership for AI-Driven Business Transformation: A Cross-Industry Framework for 
Technology Executives. DBA Thesis. Kennedy University of Baptist, France.
════════════════════════════════════════════════

END OF REPORT
"""


def build_user_prompt(
    challenge: str,
    role: str = "Technology Executive",
    industry: str = "Not specified",
) -> str:
    """
    Build the user-facing prompt with the executive's specific challenge.

    Args:
        challenge: The executive's AI transformation challenge description.
        role:      The executive's role (e.g., CIO, CTO).
        industry:  The industry sector (e.g., Healthcare, Financial Services).

    Returns:
        Formatted user prompt string.
    """
    role = role.strip() if role.strip() else "Technology Executive"
    industry = industry.strip() if industry.strip() else "Not specified"

    return f"""Please provide a complete CISLF Strategic Analysis Report for the 
following AI transformation challenge.

EXECUTIVE ROLE: {role}
INDUSTRY / SECTOR: {industry}

AI TRANSFORMATION CHALLENGE:
{challenge.strip()}

Analyse this challenge through each of the four CISLF pillars and produce the 
full report in the exact format specified in your instructions. 
Replace {{ROLE}} with "{role}" and {{INDUSTRY}} with "{industry}" in the header.
Ensure all scores are numeric (e.g., 7.5) and consistent between pillar sections 
and the maturity scorecard. Provide specific, actionable recommendations tailored 
to the described situation — avoid generic advice.
"""


# ---------------------------------------------------------------------------
# Report Validation
# ---------------------------------------------------------------------------

def validate_report(report_text: str) -> tuple[bool, list[str]]:
    """
    Validate that the LLM-generated report contains all mandatory sections.

    Args:
        report_text: The raw text output from the LLM.

    Returns:
        Tuple of (is_valid: bool, missing_sections: list[str]).
        If is_valid is True, missing_sections is an empty list.
    """
    if not report_text or len(report_text.strip()) < 200:
        return False, ["Report is too short or empty."]

    missing = []
    for section in MANDATORY_SECTIONS:
        if section.upper() not in report_text.upper():
            missing.append(section)

    return (len(missing) == 0), missing


# ---------------------------------------------------------------------------
# Section Parsing Utilities
# ---------------------------------------------------------------------------

def extract_section(report_text: str, start_marker: str, end_marker: Optional[str] = None) -> str:
    """
    Extract a section of text between start_marker and end_marker.

    Args:
        report_text:  Full report text.
        start_marker: String that marks the beginning of the section.
        end_marker:   String that marks the end (exclusive). If None, extracts to end of text.

    Returns:
        Extracted section text, or empty string if not found.
    """
    text_upper = report_text.upper()
    start_idx = text_upper.find(start_marker.upper())
    if start_idx == -1:
        return ""

    # Move past the start marker itself
    content_start = start_idx + len(start_marker)

    if end_marker:
        end_idx = text_upper.find(end_marker.upper(), content_start)
        if end_idx == -1:
            return report_text[content_start:].strip()
        return report_text[content_start:end_idx].strip()

    return report_text[content_start:].strip()


def get_maturity_status(score: float) -> str:
    """
    Return the maturity status label for a given numeric score.

    Args:
        score: Numeric score between 0 and 10.

    Returns:
        Status string (e.g., "Strong", "Exemplary").
    """
    for low, high, label in MATURITY_LEVELS:
        if low <= score <= high:
            return label
    return "Unknown"


def get_maturity_color(score: float) -> str:
    """
    Return a hex color code corresponding to a maturity score.
    Used for progress bars and indicators in the UI.
    """
    if score < 4:
        return "#D62828"    # Red — Critical Attention
    elif score < 5.5:
        return "#F77F00"    # Orange — Needs Development
    elif score < 7:
        return "#F4D03F"    # Yellow — Developing
    elif score < 8.5:
        return "#40916C"    # Green — Strong
    else:
        return "#1B4332"    # Dark Green — Exemplary


import re

def parse_cislf_report(report_text: str) -> dict:
    """
    Parse a canonical CISLF Framework report string into a structured dictionary.
    Includes robust fallbacks if sections are missing or formatted slightly differently.
    """
    parsed = {
        "is_parsed": False,
        "raw_text": report_text,
        "executive_summary": "",
        "readiness_score": 0.0,
        "readiness_justification": "",
        "pillars": {},
        "action_plan": {
            "month1": [],
            "month2": [],
            "month3": []
        },
        "risks": [],
        "priority_actions": [],
        "scorecard": {}
    }
    
    if not report_text:
        return parsed

    def extract_between(text: str, start: str, end: str) -> str:
        tu = text.upper()
        s = tu.find(start.upper())
        if s == -1:
            return ""
        s += len(start)
        e = tu.find(end.upper(), s)
        return text[s:e].strip() if e != -1 else text[s:].strip()

    # 1. Executive Summary & Readiness Score
    exec_summary_raw = extract_between(report_text, "EXECUTIVE SUMMARY", "TRANSFORMATION READINESS SCORE:")
    exec_summary_lines = [line.strip() for line in exec_summary_raw.splitlines() if line.strip() and not all(c in "-─=═" for c in line.strip())]
    parsed["executive_summary"] = "\n".join(exec_summary_lines)

    # Readiness Score
    readiness_line = ""
    tu = report_text.upper()
    score_idx = tu.find("TRANSFORMATION READINESS SCORE:")
    if score_idx != -1:
        end_line_idx = report_text.find("\n", score_idx)
        if end_line_idx != -1:
            readiness_line = report_text[score_idx:end_line_idx]
            match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", readiness_line)
            if match:
                parsed["readiness_score"] = float(match.group(1))
        
        next_sec_idx = tu.find("PILLAR 1", score_idx)
        if next_sec_idx != -1:
            just_raw = report_text[score_idx + len("TRANSFORMATION READINESS SCORE:"):next_sec_idx].strip()
            just_lines = [l.strip() for l in just_raw.splitlines() if l.strip() and not all(c in "-─=═" for c in l.strip())]
            if just_lines and "/" in just_lines[0] and len(just_lines[0]) < 20:
                just_lines = just_lines[1:]
            parsed["readiness_justification"] = " ".join(just_lines)

    # 2. Pillars 1 to 4
    pillar_markers = [
        ("PILLAR 1", "PILLAR 2"),
        ("PILLAR 2", "PILLAR 3"),
        ("PILLAR 3", "PILLAR 4"),
        ("PILLAR 4", "90-DAY ACTION PLAN")
    ]
    
    pillar_titles = {
        1: "Leadership Mindset & Vision",
        2: "Strategic Business-Technology Alignment",
        3: "Organisational Capability & Culture",
        4: "Responsible AI Governance"
    }

    for idx, (curr_m, next_m) in enumerate(pillar_markers, 1):
        p_text = extract_between(report_text, curr_m, next_m)
        if not p_text:
            continue
        
        p_dict = {
            "title": pillar_titles[idx],
            "assessment": "",
            "strengths": [],
            "gaps": [],
            "recommendations": [],
            "score": 0.0
        }
        
        p_dict["assessment"] = extract_between(p_text, "ASSESSMENT:", "STRENGTHS IDENTIFIED:")
        p_dict["assessment"] = " ".join([l.strip() for l in p_dict["assessment"].splitlines() if l.strip()])
        
        strengths_raw = extract_between(p_text, "STRENGTHS IDENTIFIED:", "CRITICAL GAPS:")
        p_dict["strengths"] = [l.lstrip("•-* ").strip() for l in strengths_raw.splitlines() if l.strip() and l.lstrip("•-* ").strip()]
        
        gaps_raw = extract_between(p_text, "CRITICAL GAPS:", "STRATEGIC RECOMMENDATIONS:")
        p_dict["gaps"] = [l.lstrip("•-* ").strip() for l in gaps_raw.splitlines() if l.strip() and l.lstrip("•-* ").strip()]
        
        recs_raw = extract_between(p_text, "STRATEGIC RECOMMENDATIONS:", "PILLAR SCORE:")
        p_dict["recommendations"] = [l.lstrip("•-* ").strip() for l in recs_raw.splitlines() if l.strip() and l.lstrip("•-* ").strip()]
        
        score_idx = p_text.upper().find("PILLAR SCORE:")
        if score_idx != -1:
            score_line = p_text[score_idx:]
            match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", score_line)
            if match:
                p_dict["score"] = float(match.group(1))
                
        parsed["pillars"][idx] = p_dict

    # 3. 90-Day Action Plan
    plan_raw = extract_between(report_text, "90-DAY ACTION PLAN", "RISK ASSESSMENT")
    if plan_raw:
        m1_raw = extract_between(plan_raw, "MONTH 1", "MONTH 2")
        m2_raw = extract_between(plan_raw, "MONTH 2", "MONTH 3")
        m3_raw = extract_between(plan_raw, "MONTH 3", "RISK ASSESSMENT")
        if not m3_raw:
            m3_raw = plan_raw[plan_raw.upper().find("MONTH 3"):] if plan_raw.upper().find("MONTH 3") != -1 else ""
            
        def clean_bullets(text: str) -> list[str]:
            lines = []
            for l in text.splitlines():
                l_clean = l.strip()
                if not l_clean or all(c in "-─=═" for c in l_clean) or (":" in l_clean and ("FOUNDATION" in l_clean.upper() or "ACCELERATION" in l_clean.upper() or "INTEGRATION" in l_clean.upper())):
                    continue
                lines.append(l_clean.lstrip("•-* ").strip())
            return [line for line in lines if line]

        parsed["action_plan"]["month1"] = clean_bullets(m1_raw)
        parsed["action_plan"]["month2"] = clean_bullets(m2_raw)
        parsed["action_plan"]["month3"] = clean_bullets(m3_raw)

    # 4. Risk Assessment
    risks_raw = extract_between(report_text, "RISK ASSESSMENT", "TOP 5 PRIORITY ACTIONS")
    if risks_raw:
        risk_blocks = re.split(r"RISK\s*\d+\s*:", risks_raw, flags=re.IGNORECASE)
        for r_block in risk_blocks[1:]:
            lines = [l.strip() for l in r_block.splitlines() if l.strip()]
            if not lines:
                continue
            
            risk_info = {
                "name": lines[0].strip(),
                "probability": "Medium",
                "impact": "Medium",
                "description": "",
                "mitigation": ""
            }
            
            prob_impact_line = ""
            desc_start_idx = 1
            for idx, l in enumerate(lines[1:], 1):
                if "probability" in l.lower() or "impact" in l.lower():
                    prob_impact_line = l
                    desc_start_idx = idx + 1
                    break
            
            if prob_impact_line:
                match_prob = re.search(r"probability:\s*([a-zA-Z]+)", prob_impact_line, re.IGNORECASE)
                match_imp = re.search(r"impact:\s*([a-zA-Z]+)", prob_impact_line, re.IGNORECASE)
                if match_prob:
                    risk_info["probability"] = match_prob.group(1).capitalize()
                if match_imp:
                    risk_info["impact"] = match_imp.group(1).capitalize()
            
            desc_lines = []
            mit_lines = []
            in_mitigation = False
            for l in lines[desc_start_idx:]:
                if l.upper().startswith("MITIGATION:"):
                    in_mitigation = True
                    mit_lines.append(l[len("MITIGATION:"):].strip())
                elif in_mitigation:
                    mit_lines.append(l)
                else:
                    if l.upper().startswith("DESCRIPTION:"):
                        desc_lines.append(l[len("DESCRIPTION:"):].strip())
                    else:
                        desc_lines.append(l)
            
            risk_info["description"] = " ".join(desc_lines)
            risk_info["mitigation"] = " ".join(mit_lines)
            parsed["risks"].append(risk_info)

    # 5. Top 5 Priority Actions
    priorities_raw = extract_between(report_text, "TOP 5 PRIORITY ACTIONS", "CISLF MATURITY SCORECARD")
    if priorities_raw:
        p_blocks = re.split(r"\n\s*\d+\s*\.\s*", "\n" + priorities_raw)
        for p_block in p_blocks[1:]:
            lines = [l.strip() for l in p_block.splitlines() if l.strip()]
            if not lines:
                continue
            
            header_line = lines[0]
            parts = header_line.split("|")
            title = parts[0].strip()
            pillar_ref = ""
            timeline = ""
            for part in parts[1:]:
                part_clean = part.strip()
                if "pillar" in part_clean.lower():
                    pillar_ref = part_clean.split(":")[-1].strip()
                elif "timeline" in part_clean.lower() or "days" in part_clean.lower():
                    timeline = part_clean.split(":")[-1].strip()
            
            desc = " ".join(lines[1:])
            parsed["priority_actions"].append({
                "title": title,
                "pillar": pillar_ref,
                "timeline": timeline,
                "description": desc
            })

    if parsed["pillars"]:
        parsed["is_parsed"] = True

    return parsed
