import os
import fitz
import tempfile
import pandas as pd
from datetime import datetime

def generate_premium_pdf(parsed: dict, role: str, industry: str, radar_path: str, bar_path: str, source: str = "AI") -> bytes:
    """Generate a highly styled, multi-page PDF using PyMuPDF's Story API."""
    
    # ── 1. Construct HTML & CSS ──────────────────────────────────────────
    css = """
    body {
        font-family: Helvetica, sans-serif;
        color: #2D3748;
        font-size: 11pt;
        line-height: 1.5;
    }
    .cover {
        background-color: #1B4332;
        color: white;
        padding: 40px;
        border-radius: 8px;
        margin-bottom: 30px;
    }
    .cover h1 {
        color: white;
        font-size: 26pt;
        margin-bottom: 5px;
    }
    .cover .subtitle {
        color: #95D5B2;
        font-size: 14pt;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .cover p {
        color: #D8F3DC;
        font-size: 11pt;
        margin: 5px 0;
    }
    h2 {
        color: #1B4332;
        border-bottom: 2px solid #52B788;
        padding-bottom: 5px;
        font-size: 16pt;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    h3 {
        color: #2D6A4F;
        font-size: 13pt;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    .readiness {
        background-color: #F0FAF4;
        border-left: 5px solid #2D6A4F;
        padding: 15px;
        margin: 15px 0;
    }
    .readiness h3 {
        margin-top: 0;
        color: #1B4332;
    }
    .readiness p {
        margin-bottom: 0;
        font-style: italic;
        color: #2D6A4F;
    }
    .charts-container {
        text-align: center;
        margin-bottom: 20px;
    }
    .pillar-box {
        background-color: #FAFFFE;
        border: 1px solid #D8F3DC;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 6px;
    }
    .sbox {
        padding: 10px;
        margin-top: 10px;
        border-radius: 4px;
    }
    .sbox-s { background-color: #EAF7ED; border: 1px solid #C2ECD0; }
    .sbox-g { background-color: #FFF5EC; border: 1px solid #FFE3CC; }
    .sbox-r { background-color: #F0F7FF; border: 1px solid #CBE3FF; }
    .sbox-title {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .sbox-s .sbox-title { color: #2D6A4F; }
    .sbox-g .sbox-title { color: #B25E00; }
    .sbox-r .sbox-title { color: #004B8C; }
    ul {
        margin: 0;
        padding-left: 20px;
    }
    li { margin-bottom: 4px; }
    .table-risk {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    .table-risk th {
        background-color: #1B4332;
        color: white;
        padding: 8px;
        text-align: left;
    }
    .table-risk td {
        border: 1px solid #E2E8F0;
        padding: 8px;
    }
    .badge {
        font-weight: bold;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 9pt;
    }
    .high { color: #C0392B; }
    .medium { color: #856404; }
    .low { color: #1B4332; }
    .priority {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 10px;
        margin-bottom: 10px;
    }
    .scorecard {
        width: 100%;
        border-collapse: collapse;
    }
    .scorecard th {
        background-color: #E8F5E9;
        color: #1B4332;
        padding: 8px;
        border: 1px solid #C8E6C9;
        text-align: left;
    }
    .scorecard td {
        border: 1px solid #E2E8F0;
        padding: 8px;
    }
    .total-row {
        background-color: #D8F3DC;
        font-weight: bold;
    }
    """
    
    def render_badge(val):
        v = str(val).lower()
        cls = "high" if "high" in v else ("medium" if "med" in v else "low")
        return f'<span class="badge {cls}">{val}</span>'

    # Build HTML content
    h = []
    
    source_str = "🤖 AI Consultation" if source == "AI" else "📋 Manual Assessment"
    
    # Cover
    h.append(f"""
    <div class="cover">
        <h1>Cogni CISLF Advisor</h1>
        <div class="subtitle">Strategic Leadership & AI Transformation Report</div>
        <p><strong>Prepared For:</strong> {role} | {industry}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
        <p><strong>Assessment Mode:</strong> {source_str}</p>
        <p><strong>Framework:</strong> CISLF - Comprehensive Intelligent Strategic Leadership Framework</p>
        <p><strong>Author:</strong> Mohammad Quasif, DBA | Kennedy University of Baptist, France</p>
    </div>
    """)

    # Exec Summary & Readiness
    h.append("<h2>Executive Summary</h2>")
    h.append(f"<p>{parsed['executive_summary'].replace(chr(10), '<br>')}</p>")
    
    h.append(f"""
    <div class="readiness">
        <h3>Transformation Readiness Index: {parsed['readiness_score']}/10</h3>
        <p>{parsed['readiness_justification']}</p>
    </div>
    """)
    
    # Visuals - Use basename because Archive takes the folder
    r_base = os.path.basename(radar_path)
    b_base = os.path.basename(bar_path)
    h.append("<h2>Maturity Visualisations</h2>")
    h.append("<div class='charts-container'>")
    h.append(f"<img src='{r_base}' width='320' height='260'>")
    h.append(f"<img src='{b_base}' width='320' height='260'>")
    h.append("</div>")

    # Pillars
    h.append("<h2>Pillar Analysis</h2>")
    for num, p in parsed['pillars'].items():
        s_li = "".join(f"<li>{x}</li>" for x in p['strengths'])
        g_li = "".join(f"<li>{x}</li>" for x in p['gaps'])
        r_li = "".join(f"<li>{x}</li>" for x in p['recommendations'])
        
        h.append(f"""
        <div class="pillar-box">
            <h3>Pillar {num}: {p['title']} &nbsp;&nbsp;|&nbsp;&nbsp; Score: {p['score']}/10</h3>
            <p style="font-style:italic;">{p['assessment']}</p>
            <div class="sbox sbox-s"><div class="sbox-title">✅ Strengths Identified</div><ul>{s_li}</ul></div>
            <div class="sbox sbox-g"><div class="sbox-title">⚠️ Critical Gaps</div><ul>{g_li}</ul></div>
            <div class="sbox sbox-r"><div class="sbox-title">💡 Strategic Recommendations</div><ul>{r_li}</ul></div>
        </div>
        """)

    # 90-Day Plan
    h.append("<h2>90-Day Implementation Roadmap</h2>")
    h.append("<h3>🚀 Month 1: Foundation (Days 1-30)</h3>")
    h.append("<ul>" + "".join(f"<li>{x}</li>" for x in parsed['action_plan']['month1']) + "</ul>")
    h.append("<h3>⚡ Month 2: Acceleration (Days 31-60)</h3>")
    h.append("<ul>" + "".join(f"<li>{x}</li>" for x in parsed['action_plan']['month2']) + "</ul>")
    h.append("<h3>🔄 Month 3: Integration (Days 61-90)</h3>")
    h.append("<ul>" + "".join(f"<li>{x}</li>" for x in parsed['action_plan']['month3']) + "</ul>")

    # Risks
    h.append("<h2>🛑 Risk Assessment & Mitigation</h2>")
    risk_rows = ""
    for idx, r in enumerate(parsed['risks'], 1):
        risk_rows += f"""
        <tr>
            <td><strong>Risk {idx}: {r['name']}</strong><br>Prob: {render_badge(r['probability'])} | Impact: {render_badge(r['impact'])}</td>
            <td>{r['description']}</td>
            <td>{r['mitigation']}</td>
        </tr>
        """
    h.append(f"""
    <table class="table-risk">
        <thead><tr><th width="30%">Risk</th><th width="35%">Description</th><th width="35%">Mitigation</th></tr></thead>
        <tbody>{risk_rows}</tbody>
    </table>
    """)

    # Priorities
    h.append("<h2>🏆 Top 5 Priority Actions</h2>")
    for idx, action in enumerate(parsed['priority_actions'], 1):
        h.append(f"""
        <div class="priority">
            <strong>{idx}. {action['title']}</strong><br>
            <span style="color:#6c757d; font-size:9pt;">Pillar {action['pillar']} | Timeline: {action['timeline']}</span><br>
            {action['description']}
        </div>
        """)

    # Scorecard
    h.append("<h2>📈 CISLF Maturity Scorecard</h2>")
    sc_labels = [
        "Pillar 1: Leadership Mindset & Vision",
        "Pillar 2: Strategic Business-Tech Alignment",
        "Pillar 3: Organisational Capability & Culture",
        "Pillar 4: Responsible AI Governance"
    ]
    sc_rows = "".join(f"<tr><td>{lbl}</td><td style='text-align:right;'><strong>{parsed['pillars'][i]['score']:.1f}/10</strong></td></tr>" for i, lbl in enumerate(sc_labels, 1))
    
    h.append(f"""
    <table class="scorecard">
        <thead><tr><th>CISLF Dimension</th><th style="text-align:right;">Score</th></tr></thead>
        <tbody>
            {sc_rows}
            <tr class="total-row"><td>OVERALL CISLF MATURITY SCORE</td><td style="text-align:right;">{parsed['readiness_score']:.1f}/10</td></tr>
        </tbody>
    </table>
    """)

    # Citation
    h.append("<br><br><hr>")
    h.append("<p style='font-size:9pt; color:#6c757d; font-style:italic;'><strong>Citation:</strong> Quasif, M. (2025). Strategic Leadership for AI-Driven Business Transformation: A Cross-Industry Framework for Technology Executives. DBA Thesis. Kennedy University of Baptist, France.</p>")

    html_content = "".join(h)

    # ── 2. Render to PDF ──────────────────────────────────────────────────
    tmp_path = tempfile.mktemp(suffix=".pdf")
    writer = fitz.DocumentWriter(tmp_path)
    
    # fitz.Story requires a valid user CSS, and Archive to resolve local images
    arch = fitz.Archive(os.path.dirname(radar_path))
    story = fitz.Story(html=html_content, user_css=css, archive=arch)
    
    # Page setup
    margin = 50
    page_rect = fitz.Rect(0, 0, 595, 842)  # A4 size
    content_rect = fitz.Rect(margin, margin, 595 - margin, 842 - margin)
    
    # Layout loop
    more = 1
    while more:
        dev = writer.begin_page(page_rect)
        more, _ = story.place(content_rect)
        story.draw(dev)
        writer.end_page()
    writer.close()
    
    with open(tmp_path, "rb") as f:
        pdf_bytes = f.read()
        
    try:
        os.remove(tmp_path)
    except:
        pass

    return pdf_bytes
