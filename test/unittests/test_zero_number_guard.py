"""Regression coverage for the zero-number identity guard.

``extract_number`` returns the integer ``0`` for an utterance about the
number zero. In Python ``0 == False``, so a guard written as
``number not in (None, False)`` or ``if number:`` treats a successfully
extracted zero exactly like a failed extraction and routes to the
no-number/random path instead of speaking a fact about zero. The guard
must use identity (``is not None and is not False``), which is the only
shape that keeps 0 while still rejecting the None and False sentinels.
"""
import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

import ovos_skill_number_facts as _skill_module
from ovos_skill_number_facts import NumbersSkill


class TestZeroNumberGuard(unittest.TestCase):

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
    @patch.object(_skill_module, "number_trivia", lambda n: f"FACT_ABOUT_{n}")
    def test_extract_number_zero_speaks_number_trivia(self):
        """extract_number('fact about the number zero') returns 0. The
        skill must speak a fact about 0, not fall back to no.number.found."""
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: 0):
            skill.handle_numbers(
                Message("", {"utterance": "give me a fact about the number zero"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak"])
        self.assertEqual(self.spoken[0][1][0], "FACT_ABOUT_0")

    @patch.object(_skill_module, "random_math", lambda: "RANDOM_MATH")
    @patch.object(_skill_module, "number_math", lambda n: f"MATH_{n}")
    def test_extract_number_zero_speaks_math_trivia(self):
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: 0):
            skill.handle_math(
                Message("", {"utterance": "math fact about zero"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak"])
        self.assertEqual(self.spoken[0][1][0], "MATH_0")

    @patch.object(_skill_module, "random_year", lambda: "RANDOM_YEAR")
    @patch.object(_skill_module, "year_trivia", lambda n: f"YEAR_{n}")
    def test_extract_number_zero_speaks_year_trivia(self):
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: 0):
            skill.handle_year(
                Message("", {"utterance": "year fact about zero"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak"])
        self.assertEqual(self.spoken[0][1][0], "YEAR_0")


if __name__ == "__main__":
    unittest.main()
