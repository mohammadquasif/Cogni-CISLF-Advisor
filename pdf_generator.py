"""
pdf_generator.py — Premium CISLF Executive PDF Generator
=========================================================
Uses PyMuPDF (fitz) Story API for HTML→PDF rendering PLUS native fitz drawing
for the cover page, chart images (no-break), and page numbering.

Key design decisions:
- Cover page is drawn with fitz.Page native drawing calls → full-bleed dark gradient,
  no reliance on HTML/CSS gradient (which fitz Story does not support).
- Charts are embedded as full-width images on their own page section using fitz
  Story <img> tags pointing to a temp archive directory — this guarantees they
  never split across pages.
- Each major section (Pillar 1-4, Action Plan, Risks, Priorities, Scorecard) is
  preceded by a CSS `page-break-before: always` so sections always start cleanly.
- Page numbers are injected as a post-process on every page after the cover.
"""

import os
import io
import tempfile
import fitz
from datetime import datetime


# ---------------------------------------------------------------------------
# Colour Palette — CISLF Brand
# ---------------------------------------------------------------------------
C_DARK       = (0.051, 0.169, 0.122)   # #0D2B1F
C_FOREST     = (0.106, 0.263, 0.196)   # #1B4332
C_MID        = (0.176, 0.416, 0.310)   # #2D6A4F
C_MINT       = (0.322, 0.718, 0.533)   # #52B788
C_LIGHT_MINT = (0.847, 0.953, 0.863)   # #D8F3DC
C_WHITE      = (1.0, 1.0, 1.0)
C_OFFWHITE   = (0.980, 1.000, 0.984)   # #FAFFFE
C_LIGHT_GREY = (0.945, 0.957, 0.969)   # #F1F4F8
C_GREY       = (0.420, 0.467, 0.502)   # #6c757d
C_TEXT       = (0.180, 0.216, 0.282)   # #2D3748

# Maturity band colours (hex string and float-triple)
MATURITY_COLORS = {
    "Critical Attention":  ("#D62828", (0.839, 0.157, 0.157)),
    "Needs Development":   ("#F77F00", (0.969, 0.498, 0.000)),
    "Developing":          ("#F4D03F", (0.957, 0.816, 0.247)),
    "Strong":              ("#40916C", (0.251, 0.569, 0.424)),
    "Exemplary":           ("#1B4332", (0.106, 0.263, 0.196)),
}


def _maturity_label(score: float) -> str:
    if score < 4:   return "Critical Attention"
    if score < 5.5: return "Needs Development"
    if score < 7:   return "Developing"
    if score < 8.5: return "Strong"
    return "Exemplary"


def _score_color_hex(score: float) -> str:
    return MATURITY_COLORS[_maturity_label(score)][0]


def _score_color_rgb(score: float):
    return MATURITY_COLORS[_maturity_label(score)][1]


# ---------------------------------------------------------------------------
# Cover Page — drawn natively (no HTML)
# ---------------------------------------------------------------------------

def _draw_cover_page(doc: fitz.Document, role: str, industry: str,
                     source: str, overall_score: float,
                     logo_path: str | None = None) -> None:
    """Draw a full-bleed dark gradient cover page using native fitz drawing."""
    page = doc.new_page(width=595, height=842)   # A4

    # ── Background gradient simulation (two overlapping rects) ────────────
    page.draw_rect(fitz.Rect(0, 0, 595, 842), color=C_DARK, fill=C_DARK)
    # Subtle lighter band at the top
    page.draw_rect(fitz.Rect(0, 0, 595, 320), color=C_FOREST, fill=C_FOREST, fill_opacity=0.6)

    # ── Accent line ────────────────────────────────────────────────────────
    page.draw_line(fitz.Point(50, 290), fitz.Point(545, 290),
                   color=C_MINT, width=1.5)

    # ── CISLF label (top-left micro-badge) ────────────────────────────────
    page.draw_rect(fitz.Rect(50, 50, 180, 68), color=C_MID, fill=C_MID)
    page.insert_text(fitz.Point(57, 63), "CISLF FRAMEWORK",
                     fontsize=8, color=C_LIGHT_MINT, fontname="hebo")

    # ── Main title ────────────────────────────────────────────────────────
    page.insert_text(fitz.Point(50, 115),
                     "Cogni CISLF Advisor",
                     fontsize=30, color=C_WHITE, fontname="hebo")
    page.insert_text(fitz.Point(50, 150),
                     "Strategic Leadership & AI",
                     fontsize=18, color=C_MINT, fontname="hebo")
    page.insert_text(fitz.Point(50, 174),
                     "Transformation Report",
                     fontsize=18, color=C_MINT, fontname="hebo")

    # ── Assessment mode badge ─────────────────────────────────────────────
    mode_label = "AI Consultation" if source == "AI" else "Manual Assessment"
    mode_icon  = "AI"              if source == "AI" else "MA"
    page.draw_rect(fitz.Rect(50, 195, 175, 218), color=C_MID, fill=C_MID)
    page.insert_text(fitz.Point(57, 212),
                     f"[ {mode_icon} ]  {mode_label}",
                     fontsize=9, color=C_LIGHT_MINT, fontname="hebo")

    # ── Overall score circle ───────────────────────────────────────────────
    cx, cy, cr = 480, 160, 52
    score_rgb = _score_color_rgb(overall_score)
    page.draw_circle(fitz.Point(cx, cy), cr + 4, color=score_rgb, fill=score_rgb)
    page.draw_circle(fitz.Point(cx, cy), cr, color=C_DARK, fill=C_DARK)
    score_str = f"{overall_score:.1f}"
    page.insert_text(fitz.Point(cx - 22, cy + 10),
                     score_str,
                     fontsize=26, color=C_WHITE, fontname="hebo")
    page.insert_text(fitz.Point(cx - 13, cy + 26),
                     "/ 10",
                     fontsize=9, color=C_MINT, fontname="helv")
    mat_lbl = _maturity_label(overall_score)
    lbl_x = cx - len(mat_lbl) * 2.8
    page.insert_text(fitz.Point(lbl_x, cy + cr + 18),
                     mat_lbl,
                     fontsize=8, color=score_rgb, fontname="hebo")

    # ── Divider line ──────────────────────────────────────────────────────
    page.draw_line(fitz.Point(50, 290), fitz.Point(545, 290),
                   color=C_MINT, width=0.8)

    # ── Details block ─────────────────────────────────────────────────────
    y = 318
    details = [
        ("Prepared For",  f"{role}"),
        ("Industry",      f"{industry}"),
        ("Date",          datetime.now().strftime("%B %d, %Y")),
        ("Framework",     "Comprehensive Intelligent Strategic Leadership Framework (CISLF)"),
    ]
    for label, value in details:
        page.insert_text(fitz.Point(50, y), f"{label}:",
                         fontsize=9, color=C_MINT, fontname="hebo")
        page.insert_text(fitz.Point(160, y), value,
                         fontsize=9, color=C_OFFWHITE, fontname="helv")
        y += 20

    # ── Maturity gauge bar ─────────────────────────────────────────────────
    y_gauge = 430
    page.insert_text(fitz.Point(50, y_gauge - 14),
                     "CISLF MATURITY GAUGE",
                     fontsize=8, color=C_MINT, fontname="hebo")
    bands = [
        ("Critical", (0.839, 0.157, 0.157), 0.0, 3.9),
        ("Dev.",     (0.969, 0.498, 0.000), 4.0, 5.4),
        ("Progress", (0.957, 0.816, 0.247), 5.5, 6.9),
        ("Strong",   (0.251, 0.569, 0.424), 7.0, 8.4),
        ("Exemplary",(0.106, 0.263, 0.196), 8.5, 10.0),
    ]
    gauge_x0, gauge_x1 = 50, 545
    gauge_w = gauge_x1 - gauge_x0
    gauge_h = 18
    for lbl, rgb, lo, hi in bands:
        x0 = gauge_x0 + (lo / 10.0) * gauge_w
        x1 = gauge_x0 + (min(hi, 10.0) / 10.0) * gauge_w
        page.draw_rect(fitz.Rect(x0, y_gauge, x1, y_gauge + gauge_h),
                       color=rgb, fill=rgb)
        page.insert_text(fitz.Point(x0 + 3, y_gauge + 12),
                         lbl, fontsize=6, color=C_WHITE, fontname="helv")
    # Marker for current score
    marker_x = gauge_x0 + (min(overall_score, 10.0) / 10.0) * gauge_w
    page.draw_line(fitz.Point(marker_x, y_gauge - 8),
                   fitz.Point(marker_x, y_gauge + gauge_h + 8),
                   color=C_WHITE, width=2.5)
    page.draw_circle(fitz.Point(marker_x, y_gauge - 10), 5,
                     color=C_WHITE, fill=C_WHITE)

    # ── Pillar summary table on cover ──────────────────────────────────────
    y_table = y_gauge + gauge_h + 40
    page.insert_text(fitz.Point(50, y_table - 12),
                     "PILLAR SCORES AT A GLANCE",
                     fontsize=8, color=C_MINT, fontname="hebo")

    # Draw table inline — scores inserted by caller via _draw_cover_pillar_row
    return page   # caller will add pillar rows


def _draw_cover_pillar_rows(page: fitz.Page, pillar_scores: dict) -> None:
    """Draw the 4 pillar score rows on the cover page."""
    pillar_names = {
        1: "P1  Leadership Mindset & Vision",
        2: "P2  Strategic Biz-Tech Alignment",
        3: "P3  Organisational Capability & Culture",
        4: "P4  Responsible AI Governance",
    }
    y_gauge = 430
    gauge_h = 18
    y_table = y_gauge + gauge_h + 40

    for i, (p_num, p_name) in enumerate(pillar_names.items()):
        score = pillar_scores.get(p_num, 0.0)
        sc_rgb = _score_color_rgb(score)
        sc_lbl = _maturity_label(score)
        row_y = y_table + i * 30
        # Name
        page.insert_text(fitz.Point(50, row_y + 12), p_name,
                         fontsize=9, color=C_OFFWHITE, fontname="helv")
        # Score pill
        pill_x = 380
        page.draw_rect(fitz.Rect(pill_x, row_y, pill_x + 44, row_y + 18),
                       color=sc_rgb, fill=sc_rgb)
        page.insert_text(fitz.Point(pill_x + 4, row_y + 12),
                         f"{score:.1f}/10",
                         fontsize=8, color=C_WHITE, fontname="hebo")
        # Status label
        page.insert_text(fitz.Point(432, row_y + 12), sc_lbl,
                         fontsize=8, color=sc_rgb, fontname="helv")

    # Bottom citation
    page.insert_text(fitz.Point(50, 780),
                     "Quasif, M. (2026). Strategic Leadership for AI-Driven Business Transformation: A Cross-Industry Framework for",
                     fontsize=7.5, color=C_GREY, fontname="helv")
    page.insert_text(fitz.Point(50, 793),
                     "Technology Executives. DBA in AI Thesis (Research Tenure: 2024-2026). Global Knowledge Hub, Kennedy University. Supervisor: Prof. Dr. Joseph Kwaku Mihaye.",
                     fontsize=7.5, color=C_GREY, fontname="helv")

    page.draw_line(fitz.Point(50, 770), fitz.Point(545, 770),
                   color=C_MID, width=0.5)


# ---------------------------------------------------------------------------
# Page header + footer helpers (injected post-render)
# ---------------------------------------------------------------------------

def _add_header_footer(page: fitz.Page, page_num: int, role: str) -> None:
    """Add a subtle header and page-number footer to content pages (not cover)."""
    W = page.rect.width
    # Header line
    page.draw_line(fitz.Point(40, 32), fitz.Point(W - 40, 32),
                   color=C_MINT, width=0.6)
    page.insert_text(fitz.Point(42, 27),
                     "CISLF Strategic Analysis Report  |  Confidential",
                     fontsize=7, color=C_GREY, fontname="helv")
    page.insert_text(fitz.Point(W - 80, 27),
                     role[:30],
                     fontsize=7, color=C_GREY, fontname="helv")

    # Footer line
    page.draw_line(fitz.Point(40, 820), fitz.Point(W - 40, 820),
                   color=C_LIGHT_MINT, width=0.5)
    page.insert_text(fitz.Point(42, 833),
                     "Cogni CISLF Advisor  |  Mohammad Quasif, DBA in AI Candidate  |  Research Tenure: 2024-2026  |  Kennedy University",
                     fontsize=7, color=C_GREY, fontname="helv")
    page.insert_text(fitz.Point(W - 60, 833),
                     f"Page {page_num}",
                     fontsize=7, color=C_GREY, fontname="hebo")


# ---------------------------------------------------------------------------
# CSS for Story pages
# ---------------------------------------------------------------------------

_STORY_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

body {
    font-family: Helvetica, Arial, sans-serif;
    color: #2D3748;
    font-size: 10.5pt;
    line-height: 1.55;
    margin: 0;
    padding: 0;
}

/* ── Section headings ─────────────────────────────────────── */
h2 {
    color: #1B4332;
    font-size: 14pt;
    font-weight: bold;
    border-bottom: 2px solid #52B788;
    padding-bottom: 5px;
    margin-top: 22px;
    margin-bottom: 12px;
    page-break-before: always;
    page-break-after: avoid;
    page-break-inside: avoid;
}
h2.no-break { page-break-before: auto; }

h3 {
    color: #2D6A4F;
    font-size: 11.5pt;
    font-weight: bold;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
    page-break-inside: avoid;
}

/* ── Executive summary block ──────────────────────────────── */
.exec-box {
    background-color: #F8FFFB;
    border-left: 5px solid #1B4332;
    padding: 14px 16px;
    margin: 12px 0;
    page-break-inside: avoid;
}

/* ── Readiness score box ──────────────────────────────────── */
.readiness {
    background-color: #E8F5E9;
    border-left: 5px solid #2D6A4F;
    padding: 12px 15px;
    margin: 12px 0;
    page-break-inside: avoid;
}
.readiness-score {
    font-size: 14pt;
    font-weight: bold;
    color: #1B4332;
    margin: 0 0 6px 0;
}
.readiness p { margin: 0; color: #2D6A4F; font-style: italic; }

/* ── Chart image wrapper — never breaks ───────────────────── */
.chart-wrap {
    text-align: center;
    margin: 8px 0 16px 0;
    page-break-inside: avoid;
}
.chart-wrap img {
    max-width: 100%;
    height: auto;
}
.chart-section {
    page-break-inside: avoid;
}

/* ── Pillar boxes ─────────────────────────────────────────── */
.pillar-box {
    background-color: #FAFFFE;
    border: 1px solid #D8F3DC;
    border-left: 5px solid #52B788;
    padding: 14px 15px;
    margin-bottom: 14px;
    border-radius: 6px;
    page-break-inside: avoid;
}
.pillar-title {
    font-size: 12pt;
    font-weight: bold;
    color: #1B4332;
    margin: 0 0 8px 0;
}
.pillar-score-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 10pt;
    margin-left: 8px;
}

/* ── Strength / Gap / Rec sub-boxes ───────────────────────── */
.sbox {
    padding: 9px 11px;
    margin-top: 9px;
    border-radius: 4px;
    page-break-inside: avoid;
}
.sbox-s { background-color: #EAF7ED; border: 1px solid #C2ECD0; }
.sbox-g { background-color: #FFF5EC; border: 1px solid #FFE3CC; }
.sbox-r { background-color: #F0F7FF; border: 1px solid #CBE3FF; }
.sbox-title {
    font-weight: bold;
    font-size: 10pt;
    margin-bottom: 5px;
}
.sbox-s .sbox-title { color: #2D6A4F; }
.sbox-g .sbox-title { color: #B25E00; }
.sbox-r .sbox-title { color: #004B8C; }

ul { margin: 0; padding-left: 18px; }
li { margin-bottom: 4px; }

/* ── Risk table ───────────────────────────────────────────── */
.table-risk {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
    page-break-inside: avoid;
}
.table-risk th {
    background-color: #1B4332;
    color: white;
    padding: 7px 8px;
    text-align: left;
    font-size: 9.5pt;
}
.table-risk td {
    border: 1px solid #E2E8F0;
    padding: 7px 8px;
    font-size: 9.5pt;
    vertical-align: top;
}

/* ── Priority action rows ─────────────────────────────────── */
.priority-row {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #52B788;
    padding: 9px 11px;
    margin-bottom: 8px;
    border-radius: 4px;
    page-break-inside: avoid;
}
.priority-meta {
    color: #6c757d;
    font-size: 8.5pt;
    margin-bottom: 3px;
}
.priority-desc { font-size: 9.5pt; color: #2D3748; }

/* ── Scorecard table ──────────────────────────────────────── */
.scorecard {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    page-break-inside: avoid;
}
.scorecard th {
    background-color: #E8F5E9;
    color: #1B4332;
    padding: 7px;
    border: 1px solid #C8E6C9;
    text-align: left;
    font-size: 9.5pt;
}
.scorecard td {
    border: 1px solid #E2E8F0;
    padding: 7px;
    font-size: 9.5pt;
}
.total-row { background-color: #D8F3DC; font-weight: bold; }

/* ── Methodology section ──────────────────────────────────── */
.method-box {
    background: #0F2027;
    color: #E0E0E0;
    border-radius: 6px;
    padding: 12px 14px;
    margin-bottom: 12px;
    page-break-inside: avoid;
}
.method-box h3 { color: #64B5F6; margin-top: 0; font-size: 10.5pt; }

/* ── Citation footer ──────────────────────────────────────── */
.citation {
    font-size: 8pt;
    color: #6c757d;
    font-style: italic;
    margin-top: 20px;
    padding-top: 10px;
    border-top: 1px solid #E2E8F0;
}
"""


# ---------------------------------------------------------------------------
# HTML Builders
# ---------------------------------------------------------------------------

def _badge(score: float) -> str:
    color = _score_color_hex(score)
    lbl   = _maturity_label(score)
    return (f'<span class="pillar-score-badge" '
            f'style="background:{color}20;color:{color};border:1px solid {color}60;">'
            f'{score:.1f}/10 — {lbl}</span>')


def _risk_badge(val: str) -> str:
    v = val.upper()
    if v == "HIGH":   return f'<span style="color:#C0392B;font-weight:bold;">{val}</span>'
    if v == "MEDIUM": return f'<span style="color:#856404;font-weight:bold;">{val}</span>'
    return f'<span style="color:#1B4332;font-weight:bold;">{val}</span>'


def _build_html(parsed: dict, role: str, industry: str,
                source: str, radar_basename: str, bar_basename: str) -> str:
    """Build full HTML body for the Story renderer (after the cover page)."""
    h = []

    source_str = "AI Consultation" if source == "AI" else "Manual Assessment"

    # ── Executive Summary ────────────────────────────────────────────────
    h.append('<h2 class="no-break">Executive Summary</h2>')
    h.append(f'<div class="exec-box"><p>{parsed["executive_summary"].replace(chr(10), "<br>")}</p></div>')

    # ── Readiness Score ──────────────────────────────────────────────────
    score_color = _score_color_hex(parsed["readiness_score"])
    h.append(f"""
    <div class="readiness">
        <p class="readiness-score">
            Transformation Readiness Score:
            <span style="color:{score_color};">&nbsp;{parsed['readiness_score']:.1f} / 10
            &nbsp;— {_maturity_label(parsed['readiness_score'])}</span>
        </p>
        <p>{parsed['readiness_justification']}</p>
    </div>
    """)

    # ── Charts (no-break wrapper, images on same page) ───────────────────
    h.append('<h2 class="no-break">Maturity Visualisations</h2>')
    h.append('<div class="chart-section">')
    h.append('<div class="chart-wrap">')
    h.append(f'<img src="{radar_basename}" width="240" height="200">&nbsp;&nbsp;&nbsp;')
    h.append(f'<img src="{bar_basename}" width="240" height="200">')
    h.append('</div></div>')

    # ── Pillars ──────────────────────────────────────────────────────────
    h.append('<h2>Pillar Analysis</h2>')
    icons = {1: "🧠", 2: "🔗", 3: "🏗️", 4: "⚖️"}
    for num, p in parsed["pillars"].items():
        icon   = icons.get(num, "")
        s_li   = "".join(f"<li>{x}</li>" for x in p["strengths"])
        g_li   = "".join(f"<li>{x}</li>" for x in p["gaps"])
        r_li   = "".join(f"<li>{x}</li>" for x in p["recommendations"])
        badge  = _badge(p["score"])
        h.append(f"""
        <div class="pillar-box">
            <p class="pillar-title">{icon} Pillar {num}: {p['title']} {badge}</p>
            <p style="font-style:italic; color:#4a5568; margin:0 0 6px 0;">{p['assessment']}</p>
            <div class="sbox sbox-s"><div class="sbox-title">✅ Strengths Identified</div><ul>{s_li}</ul></div>
            <div class="sbox sbox-g"><div class="sbox-title">⚠️ Critical Gaps</div><ul>{g_li}</ul></div>
            <div class="sbox sbox-r"><div class="sbox-title">💡 Strategic Recommendations</div><ul>{r_li}</ul></div>
        </div>
        """)

    # ── 90-Day Action Plan ───────────────────────────────────────────────
    h.append('<h2>90-Day Implementation Roadmap</h2>')
    months = [
        ("🚀", "Month 1: Foundation",    "Days 1-30",   parsed["action_plan"]["month1"]),
        ("⚡", "Month 2: Acceleration",  "Days 31-60",  parsed["action_plan"]["month2"]),
        ("🔗", "Month 3: Integration",   "Days 61-90",  parsed["action_plan"]["month3"]),
    ]
    for icon, title, period, items in months:
        li_html = "".join(f"<li>{item}</li>" for item in items)
        h.append(f"""
        <div style="background:#FAFFFE;border:1px solid #D8F3DC;border-left:4px solid #1B4332;
                    padding:12px 14px;margin-bottom:12px;border-radius:4px;page-break-inside:avoid;">
            <p style="margin:0 0 6px 0;font-weight:bold;color:#1B4332;font-size:11pt;">
                {icon} {title}
                <span style="font-size:8pt;background:#E8F5E9;color:#2D6A4F;
                             padding:1px 6px;border-radius:3px;margin-left:6px;">{period}</span>
            </p>
            <ul style="margin:0;padding-left:16px;">{li_html}</ul>
        </div>
        """)

    # ── Risk Assessment ──────────────────────────────────────────────────
    h.append('<h2>Risk Assessment &amp; Mitigation</h2>')
    risk_rows = ""
    for idx, r in enumerate(parsed["risks"], 1):
        risk_rows += f"""
        <tr>
            <td><strong>Risk {idx}: {r['name']}</strong><br>
                Prob: {_risk_badge(r['probability'])} &nbsp;|&nbsp;
                Impact: {_risk_badge(r['impact'])}</td>
            <td>{r['description']}</td>
            <td>{r['mitigation']}</td>
        </tr>"""
    h.append(f"""
    <table class="table-risk">
        <thead><tr>
            <th width="30%">Risk</th>
            <th width="35%">Description</th>
            <th width="35%">Mitigation</th>
        </tr></thead>
        <tbody>{risk_rows}</tbody>
    </table>
    """)

    # ── Priority Actions ─────────────────────────────────────────────────
    h.append('<h2>Top 5 Priority Actions</h2>')
    for idx, act in enumerate(parsed["priority_actions"], 1):
        h.append(f"""
        <div class="priority-row">
            <p style="margin:0 0 3px 0;font-weight:bold;color:#1B4332;font-size:10.5pt;">
                {idx}. {act['title']}
            </p>
            <p class="priority-meta">Pillar {act['pillar']} &nbsp;|&nbsp; Timeline: {act['timeline']}</p>
            <p class="priority-desc">{act['description']}</p>
        </div>
        """)

    # ── Maturity Scorecard ───────────────────────────────────────────────
    h.append('<h2>CISLF Maturity Scorecard</h2>')
    sc_labels = [
        "Pillar 1 — Leadership Mindset & Vision",
        "Pillar 2 — Strategic Business-Tech Alignment",
        "Pillar 3 — Organisational Capability & Culture",
        "Pillar 4 — Responsible AI Governance",
    ]
    sc_rows = ""
    for i, lbl in enumerate(sc_labels, 1):
        p_score = parsed["pillars"].get(i, {}).get("score", 0.0)
        sc_color = _score_color_hex(p_score)
        sc_lbl   = _maturity_label(p_score)
        sc_rows += (f"<tr>"
                    f"<td>{lbl}</td>"
                    f"<td style='text-align:right;font-weight:bold;color:{sc_color}'>"
                    f"{p_score:.1f}/10</td>"
                    f"<td style='color:{sc_color};font-weight:600;'>{sc_lbl}</td>"
                    f"</tr>")
    ov = parsed["readiness_score"]
    ov_col = _score_color_hex(ov)
    sc_rows += (f"<tr class='total-row'>"
                f"<td>OVERALL CISLF MATURITY SCORE</td>"
                f"<td style='text-align:right;color:{ov_col};font-size:12pt;'>{ov:.1f}/10</td>"
                f"<td style='color:{ov_col};font-weight:700;'>{_maturity_label(ov)}</td>"
                f"</tr>")
    h.append(f"""
    <table class="scorecard">
        <thead><tr>
            <th>CISLF Dimension</th>
            <th style="text-align:right;">Score</th>
            <th>Status</th>
        </tr></thead>
        <tbody>{sc_rows}</tbody>
    </table>
    """)

    # ── Citation ─────────────────────────────────────────────────────────
    h.append("""
    <div class="citation">
        <strong>Citation:</strong> Quasif, M. (2026). Strategic Leadership for AI-Driven
        Business Transformation: A Cross-Industry Framework for Technology Executives.
        DBA in AI Thesis (Research Tenure: 2024-2026). Global Knowledge Hub, Kennedy University. Supervisor: Prof. Dr. Joseph Kwaku Mihaye. Graduation: July 2026.
    </div>
    """)

    return "".join(h)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def generate_premium_pdf(parsed: dict, role: str, industry: str,
                         radar_path: str, bar_path: str,
                         source: str = "AI") -> bytes:
    """
    Generate a premium multi-page A4 PDF.

    Strategy:
      1. Create a fitz.Document.
      2. Draw the cover page natively (dark gradient, score circle, gauge).
      3. Use fitz.Story to render all HTML content pages into the same document.
      4. Post-process each content page to add header + footer.
    """
    role     = role.strip()     or "Technology Executive"
    industry = industry.strip() or "Not specified"

    # ── Derive overall score ──────────────────────────────────────────────
    overall = parsed.get("readiness_score", 0.0)

    # ── Pillar scores dict for cover ──────────────────────────────────────
    pillar_scores = {
        num: p.get("score", 0.0)
        for num, p in parsed.get("pillars", {}).items()
    }

    # ── Build document and cover ─────────────────────────────────────────
    doc = fitz.Document()
    cover_page = _draw_cover_page(doc, role, industry, source, overall)
    _draw_cover_pillar_rows(cover_page, pillar_scores)

    # ── Prepare archive for images ────────────────────────────────────────
    img_dir      = os.path.dirname(os.path.abspath(radar_path))
    radar_base   = os.path.basename(radar_path)
    bar_base     = os.path.basename(bar_path)
    arch         = fitz.Archive(img_dir)

    # ── Build HTML content ────────────────────────────────────────────────
    html_body = _build_html(parsed, role, industry, source, radar_base, bar_base)

    # ── Render content pages via Story ────────────────────────────────────
    # Use a temporary DocumentWriter so Story can manage page layout,
    # then merge those pages into our main doc (which already has the cover).
    story = fitz.Story(html=html_body, user_css=_STORY_CSS, archive=arch)

    margin = 48
    page_rect    = fitz.Rect(0, 0, 595, 842)
    content_rect = fitz.Rect(margin, 44, 595 - margin, 830)  # room for header/footer

    tmp_path = tempfile.mktemp(suffix=".pdf")
    writer   = fitz.DocumentWriter(tmp_path)
    more = 1
    while more:
        dev  = writer.begin_page(page_rect)
        more, _ = story.place(content_rect)
        story.draw(dev)
        writer.end_page()
    writer.close()

    # Merge story pages into main doc
    story_doc = fitz.open(tmp_path)
    doc.insert_pdf(story_doc)
    story_doc.close()
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    # ── Add headers/footers to all pages after cover ──────────────────────
    total_pages = len(doc)
    short_role = role[:35] + ("…" if len(role) > 35 else "")
    for pg_idx in range(1, total_pages):   # skip cover (index 0)
        pg = doc[pg_idx]
        _add_header_footer(pg, pg_idx, short_role)

    # ── Serialise to bytes ────────────────────────────────────────────────
    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue()
