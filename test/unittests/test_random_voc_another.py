"""Regression coverage for the "another" / "one more" follow-up phrasings.

``locale/en-US/random.voc`` is the vocabulary an Adapt-style ``random``
requirement would be built from (the skill's ``handle_*`` methods already
branch on ``message.data.get("random")``). This probes that vocabulary
directly through the Adapt engine to prove "another" and "one more" resolve
to the ``random`` entity and would therefore route to the random-fact path,
without depending on any particular pipeline being active.
"""
import unittest
from os.path import dirname, join

from ovos_adapt.engine import IntentDeterminationEngine
from ovos_adapt.intent import IntentBuilder


class TestRandomVocAnother(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        voc_path = join(dirname(dirname(dirname(__file__))), "locale", "en-US", "random.voc")
        with open(voc_path, encoding="utf-8") as f:
            cls.phrases = [line.strip() for line in f if line.strip()]

        cls.engine = IntentDeterminationEngine()
        for phrase in cls.phrases:
            cls.engine.register_entity(phrase, "random")
        cls.engine.register_intent_parser(
            IntentBuilder("probe").optionally("random").build()
        )

    def test_voc_file_contains_followup_phrasings(self):
        for phrase in ("another", "one more", "give me another"):
            self.assertIn(phrase, self.phrases)

    def test_another_reaches_random_path(self):
        matches = list(self.engine.determine_intent("another"))
        self.assertTrue(matches)
        self.assertEqual(matches[0]["random"], "another")

    def test_one_more_reaches_random_path(self):
        matches = list(self.engine.determine_intent("one more"))
        self.assertTrue(matches)
        self.assertEqual(matches[0]["random"], "one more")

    def test_give_me_another_reaches_random_path(self):
        matches = list(self.engine.determine_intent("give me another"))
        self.assertTrue(matches)
        self.assertEqual(matches[0]["random"], "give me another")


if __name__ == "__main__":
    unittest.main()
