import os
import sys
import unittest

# Ensure the root of the project is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cislf_engine import validate_report, get_maturity_status, get_maturity_color
from manual_engine import calculate_all_scores, get_dynamic_questions, INDUSTRY_SCORING_CONFIG

class TestCISLFEngine(unittest.TestCase):
    def test_validate_report_valid(self):
        # A mock report with all mandatory sections present
        report_text = """
        # EXECUTIVE SUMMARY
        This is a mock summary.
        # TRANSFORMATION READINESS SCORE
        Score: 7.5
        # PILLAR 1: Leadership Mindset & Vision
        Details...
        # PILLAR 2: Strategic Business-Tech Alignment
        Details...
        # PILLAR 3: Organisational Capability & Culture
        Details...
        # PILLAR 4: Responsible AI Governance
        Details...
        # 90-DAY ACTION PLAN
        Details...
        # RISK ASSESSMENT
        Details...
        # PRIORITY ACTIONS
        Details...
        # MATURITY SCORECARD
        Details...
        # REFERENCE
        Thesis reference...
        """
        is_valid, missing = validate_report(report_text)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_validate_report_missing_sections(self):
        # A mock report missing "MATURITY SCORECARD" and "REFERENCE"
        report_text = """
        # EXECUTIVE SUMMARY
        This is a mock summary.
        # TRANSFORMATION READINESS SCORE
        Score: 7.5
        # PILLAR 1
        # PILLAR 2
        # PILLAR 3
        # PILLAR 4
        # 90-DAY ACTION PLAN
        # RISK ASSESSMENT
        # PRIORITY ACTIONS
        """
        is_valid, missing = validate_report(report_text)
        self.assertFalse(is_valid)
        self.assertIn("MATURITY SCORECARD", missing)
        self.assertIn("REFERENCE", missing)

    def test_get_maturity_status(self):
        self.assertEqual(get_maturity_status(2.5), "🔴 Critical Attention")
        self.assertEqual(get_maturity_status(4.5), "🟠 Needs Development")
        self.assertEqual(get_maturity_status(6.0), "🟡 Developing")
        self.assertEqual(get_maturity_status(8.0), "🟢 Strong")
        self.assertEqual(get_maturity_status(9.5), "✅ Exemplary")

    def test_get_maturity_color(self):
        self.assertEqual(get_maturity_color(2.5), "#D62828")  # Red
        self.assertEqual(get_maturity_color(5.0), "#F77F00")  # Orange
        self.assertEqual(get_maturity_color(6.5), "#F4D03F")  # Yellow
        self.assertEqual(get_maturity_color(8.0), "#40916C")  # Green
        self.assertEqual(get_maturity_color(9.5), "#1B4332")  # Dark Green

class TestManualEngine(unittest.TestCase):
    def test_calculate_all_scores_flat_answers(self):
        # Generate answers with all ratings set to 3 (neutral)
        answers = {}
        for p in range(1, 5):
            for q_idx in range(1, 6):
                answers[f"p{p}_q{q_idx}"] = 3

        scores, overall, breakdown = calculate_all_scores(answers, industry="Not specified")
        
        # With all answers as 3, raw scores per pillar should convert to exactly 6.0
        # (Since 3 out of 5 is 60%, which is 6.0 out of 10.0)
        for pillar, score in scores.items():
            self.assertAlmostEqual(score, 6.0, delta=0.2)
        self.assertAlmostEqual(overall, 6.0, delta=0.2)

    def test_calculate_all_scores_critical_cap(self):
        # We need an industry that has critical questions, let's use "Banking and financial services"
        # Critical questions for Banking are p4_q2 and p4_q3
        answers = {}
        # Set all answers to 4 (would be score 8.0 without caps)
        for p in range(1, 5):
            for q_idx in range(1, 6):
                answers[f"p{p}_q{q_idx}"] = 4

        # Set critical question p4_q2 to 2 (below or equal to threshold of 2)
        answers["p4_q2"] = 2

        scores, overall, breakdown = calculate_all_scores(answers, industry="Banking and financial services")
        
        # Pillar 4 score should be capped at 7.0 because critical question p4_q2 scored <= 2
        self.assertLessEqual(scores[4], 7.0)
        self.assertIn("capped at 7.0", "".join(breakdown["triggered_caps"]))

    def test_calculate_all_scores_synergy(self):
        # We need an industry with synergy configurations, e.g. "Banking and financial services"
        # Synergy pair is (2, 4)
        answers = {}
        # Set all answers to 5 (maximum, raw scores would be 10.0)
        for p in range(1, 5):
            for q_idx in range(1, 6):
                answers[f"p{p}_q{q_idx}"] = 5

        scores, overall, breakdown = calculate_all_scores(answers, industry="Banking and financial services")
        
        # Synergy pair is (2, 4). Since both base scores would be 10.0 (>= 7.5),
        # they both trigger synergy bonus of +0.3. Max score is bounded at 10.0,
        # but overall calculation includes the synergy.
        # Let's check that applied synergy metadata is populated.
        self.assertTrue(len(breakdown["applied_synergy"]) > 0)

if __name__ == "__main__":
    unittest.main()
