"""Regression coverage for random-fact fallbacks when nothing is extracted.

``extract_number`` and ``extract_datetime`` can return a falsy sentinel
(``False``/``None``) when the utterance carries no number or date. The
handlers must treat that as "nothing extracted" and fall back to a random
fact instead of forwarding the sentinel to the specific-fact fetchers or
crashing while unpacking a ``None`` result.
"""
import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

import ovos_skill_number_facts as _skill_module
from ovos_skill_number_facts import NumbersSkill


class TestRandomFallbackHandlers(unittest.TestCase):

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
    @patch.object(_skill_module, "number_trivia", lambda n: "NUMBER_FACT_%s" % n)
    def test_number_trivia_falsy_extraction_falls_back_to_random(self):
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: False):
            skill.handle_numbers(
                Message("", {"utterance": "tell me a number fact"})
            )
        spoken_facts = [call[1][0] for call in self.spoken if call[0] == "speak"]
        self.assertIn("RANDOM_FACT", spoken_facts)
        self.assertNotIn("NUMBER_FACT_False", spoken_facts)

    @patch.object(_skill_module, "random_date", lambda: "RANDOM_DATE_FACT")
    def test_date_trivia_no_date_extracted_falls_back_to_random(self):
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_datetime", lambda *a, **k: None):
            skill.handle_date(
                Message("", {"utterance": "tell me a date fact"})
            )
        spoken_facts = [call[1][0] for call in self.spoken if call[0] == "speak"]
        self.assertEqual(spoken_facts, ["RANDOM_DATE_FACT"])


if __name__ == "__main__":
    unittest.main()
