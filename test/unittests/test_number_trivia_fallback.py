"""Regression coverage for the number_trivia unparsed-number fallback path.

When ``number_trivia.intent`` fires but no number can be extracted from the
utterance, the handler falls back to a random fact. It must first speak an
explicit "couldn't find that number" acknowledgment dialog so the user isn't
silently handed an unrelated answer. That dialog must stay silent whenever a
number *is* successfully parsed.
"""
import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

import ovos_skill_number_facts as _skill_module
from ovos_skill_number_facts import NumbersSkill


class TestNumberTriviaFallbackDialog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.skill_id = "ovos-skill-number-facts.openvoiceos"

    def _make_skill(self):
        skill = NumbersSkill()
        skill._startup(FakeBus(), self.skill_id)
        skill.speak = lambda *a, **k: self.spoken.append(("speak", a, k))
        skill.speak_dialog = lambda *a, **k: self.spoken.append(("speak_dialog", a, k))
        self.spoken = []
        return skill

    @patch.object(_skill_module, "random_trivia", lambda: "RANDOM_FACT")
    @patch.object(_skill_module, "number_trivia", lambda n: "NUMBER_FACT")
    def test_no_number_extracted_speaks_apology_then_random(self):
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: None):
            skill.handle_numbers(
                Message("", {"utterance": "fact about the number of days in a year"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak_dialog", "speak"])
        self.assertEqual(self.spoken[0][1][0], "no.number.found")

    @patch.object(_skill_module, "random_trivia", lambda: "RANDOM_FACT")
    @patch.object(_skill_module, "number_trivia", lambda n: "NUMBER_FACT")
    def test_number_extracted_does_not_speak_apology(self):
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: 42):
            skill.handle_numbers(
                Message("", {"utterance": "give me a fact about the number 42"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak"])

    @patch.object(_skill_module, "random_trivia", lambda: "RANDOM_FACT")
    def test_explicit_random_request_does_not_speak_apology(self):
        skill = self._make_skill()
        skill.handle_numbers(
            Message("", {"utterance": "tell me a random number fact", "random": True})
        )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak"])


if __name__ == "__main__":
    unittest.main()
