---
title: 'Cogni CISLF Advisor: An Open-Source Executive Assessment Tool for Enterprise AI Transformation Readiness'
tags:
  - Python
  - artificial intelligence
  - enterprise governance
  - decision support
  - AI transformation
  - strategic leadership
authors:
  - name: Mohammad Quasif
    orcid: 0009-0003-9455-4804
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 16 July 2026
bibliography: paper.bib
---

# Summary

Enterprises increasingly deploy artificial intelligence (AI) systems without a
structured way to assess whether they are actually ready to scale that
deployment responsibly. Cogni CISLF Advisor is an open-source, web-based
diagnostic tool that operationalises the Comprehensive Intelligent Strategic
Leadership Framework (CISLF) — a four-pillar model covering leadership
mindset, business-technology alignment, organisational capability, and
responsible AI governance. The tool allows a technology executive to answer a
structured set of questions about a specific AI initiative and receive an
evidence-based readiness score across all four pillars, along with a
stop-redesign-scale recommendation. It is designed for non-specialist users —
CIOs, CTOs, and programme leads — rather than data scientists, and requires no
technical AI expertise to operate.

# Statement of need

Existing AI governance checklists tend to address either technical risk
(model accuracy, bias testing) or high-level policy principles (fairness,
transparency), but rarely connect these to a single, leadership-facing
decision process that an executive can apply during a portfolio review.
Cogni CISLF Advisor addresses this gap by translating the CISLF framework —
originally developed through doctoral research on AI-driven business
transformation [@quasif2026] — into a working software artefact. It targets
technology leaders in enterprise and IT services contexts who need a
repeatable, structured way to evaluate AI use cases before investment, during
pilot execution, and before enterprise-wide scaling, without requiring a data
science background to interpret the output.

# State of the field

Unlike high-level conceptual frameworks proposed by major management
consultancies (e.g., McKinsey's AI Maturity Model or Gartner's AI Maturity
Model), Cogni CISLF Advisor provides an open, reproducible self-assessment
utility. Safety-focused standards such as the NIST AI Risk Management
Framework [@nist2023] and regulatory instruments such as the EU Artificial
Intelligence Act [@eu2024aia] provide robust criteria for compliance and risk
categorization, but lack mechanisms to assess executive-level leadership
capabilities or workforce readiness. Cogni CISLF Advisor bridges this gap
by offering a structured, quantitative, and local-first evaluation that
integrates organisational capability and strategic business-technology
alignment with responsible AI governance into a single leadership-facing
decision routine.

# Software design

Cogni CISLF Advisor is built in Python using Streamlit for its interactive user interface. The backend features a dual-engine architecture: a deterministic, rule-based manual engine that evaluates twenty weighted indicators (five per pillar), and an AI Consultation engine that parses unstructured strategic challenges. Scoring logic dynamically adjusts pillar weights based on the user's industry (e.g., weighting Governance 1.4x in Banking) and applies critical question caps—soft-capping a pillar score at $7.0/10.0$ if a vital regulatory or upskilling threshold is missed—and synergy bonuses. The tool integrates multiple LLM backends (including Google Gemini, OpenAI, DeepSeek, and Anthropic Claude) via a modular adapter layer (`llm_providers.py`) with transient error handling and exponential backoff. Secure, machine-specific local credentials storage is implemented using AES-256-CBC encryption bound to the system MAC address. An automated unit test suite (`tests/test_cislf.py`) covers core scoring formulas, capping boundaries, synergy calculations, and LLM output schema validations.

# Research impact statement

Cogni CISLF Advisor serves as the primary design-science artefact
demonstrating the CISLF framework described in [@quasif2026] and its
associated framework paper [@quasif2026framework]. It shows that the
framework's four-pillar diagnostic logic can be embedded in a working tool
accessible to practitioners without requiring deep familiarity with the
underlying academic literature.

# AI usage disclosure

Generative AI tools (Anthropic Claude, accessed via an agentic coding
assistant) were used during development as implementation aids. The author
independently conceived the CISLF framework, designed the software
architecture, specified all decision structures and scoring logic, and
directed all implementation work. AI assistance was used to accelerate
coding tasks including UI styling, template generation in
`manual_engine.py`, the PDF report compiler in `pdf_generator.py`, and
test scaffolding, and to help structure prose in supporting documentation
and this paper. All AI-assisted output was reviewed, edited, fact-checked,
and validated by the author, who takes full responsibility for the accuracy
and originality of the submitted software and paper.

# Acknowledgements

The author wishes to acknowledge and thank research supervisor Prof. Dr. Joseph Kwaku Mihaye for his invaluable academic guidance and support throughout this study.

# References
