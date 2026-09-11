"""Regression coverage for the falsy-sentinel guards in NumbersSkill.

``ovos_number_parser.extract_number`` returns ``False`` (not ``None``) when
it finds no number in the utterance, and ``ovos_date_parser.extract_datetime``
returns bare ``None`` (not a tuple) when it finds no date. A guard written
against the wrong sentinel either treats a failed extraction as a success or
crashes trying to subscript ``None``.
"""
import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus

import ovos_skill_number_facts as _skill_module
from ovos_skill_number_facts import NumbersSkill


class TestFalsySentinelGuards(unittest.TestCase):

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
    def test_extract_number_false_speaks_no_number_found(self):
        """extract_number's real failure sentinel is False, not None. The
        guard must speak the 'no.number.found' dialog on False, exactly as
        it already does on None."""
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_number", lambda *a, **k: False):
            skill.handle_numbers(
                Message("", {"utterance": "fact about numbers"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak_dialog", "speak"])
        self.assertEqual(self.spoken[0][1][0], "no.number.found")

    @patch.object(_skill_module, "random_date", lambda: "RANDOM_DATE")
    def test_extract_datetime_none_does_not_raise(self):
        """extract_datetime returns bare None (not a (date, remainder)
        tuple) when it finds no date. Indexing date[0] before checking for
        None must not raise, and the skill must fall back to a random
        date fact instead."""
        skill = self._make_skill()
        with patch.object(_skill_module, "extract_datetime", lambda *a, **k: None):
            skill.handle_date(
                Message("", {"utterance": "fact about the date zzz"})
            )
        kinds = [call[0] for call in self.spoken]
        self.assertEqual(kinds, ["speak"])
        self.assertEqual(self.spoken[0][1][0], "RANDOM_DATE")


if __name__ == "__main__":
    unittest.main()
