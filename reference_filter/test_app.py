import json
import unittest
from pathlib import Path

from app import analyze_query


class AnalyzeQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases_path = Path(__file__).with_name("regression_cases.json")
        cls.cases = json.loads(cases_path.read_text(encoding="utf-8"))

    def test_attack_regressions_are_blocked(self):
        for payload in self.cases["attacks"]:
            with self.subTest(payload=payload):
                is_safe, reason = analyze_query(payload)
                self.assertFalse(is_safe, reason)

    def test_benign_regressions_are_allowed(self):
        for payload in self.cases["benign"]:
            with self.subTest(payload=payload):
                is_safe, reason = analyze_query(payload)
                self.assertTrue(is_safe, reason)

    def test_encoded_union_select_is_blocked(self):
        is_safe, _ = analyze_query("%27%20UNION%20SELECT%20NULL%2CNULL--")
        self.assertFalse(is_safe)


if __name__ == "__main__":
    unittest.main()
