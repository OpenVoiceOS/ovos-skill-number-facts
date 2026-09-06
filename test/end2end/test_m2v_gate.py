"""m2v-multilingual candidate-default gate for ovos-skill-number-facts.

Boots the skill through the candidate default intent engine -- the
model2vec multilingual classifier (``OpenVoiceOS/ovos-m2v-intents-multi-128M-v5``)
-- via ovoscope's ``get_m2v_minicroft`` and asserts, for a representative slice
of the skill's own golden utterances, the whole round trip: the correct
intent routed AND the spoken text is the real fact content, not a dialog
placeholder.

The skill fetches facts from ``numbersapi.com`` over the network; the
module-level fetchers are patched with deterministic stubs *before*
MiniCroft loads the skill, the same technique
``test/end2end/test_golden_utterances.py`` uses for the padacioso suite.
The skill calls ``self.speak(...)`` directly rather than ``speak_dialog``,
so the effect check is simply that the rendered ``utterance`` IS the
stubbed fact sentinel.
"""
import os
import shutil
import tempfile
import unittest

import ovos_skill_number_facts as _skill_module

_STUBS = {
    "number_trivia": "NUMBER_FACT",
    "random_trivia": "NUMBER_FACT",
    "number_math": "MATH_FACT",
    "random_math": "MATH_FACT",
    "date_trivia": "DATE_FACT",
    "random_date": "DATE_FACT",
    "year_trivia": "YEAR_FACT",
    "random_year": "YEAR_FACT",
}
for _name, _sentinel in _STUBS.items():
    setattr(
        _skill_module,
        _name,
        (lambda sentinel: lambda *args, **kwargs: sentinel)(_sentinel),
    )

from ovos_bus_client.message import Message  # noqa: E402
from ovos_bus_client.session import Session  # noqa: E402
from ovoscope import get_m2v_minicroft, M2V_PIPELINE  # noqa: E402

SKILL_ID = "ovos-skill-number-facts.openvoiceos"
LANG = "en-US"

_MC = None
_PIPE = None
_XDG = None
_ORIG_XDG = None


def setUpModule():
    global _MC, _PIPE, _XDG, _ORIG_XDG
    _ORIG_XDG = os.environ.get("XDG_DATA_HOME")
    _XDG = tempfile.mkdtemp(prefix="ovoscope-m2v-number-facts-xdg-")
    os.environ["XDG_DATA_HOME"] = _XDG

    _MC = get_m2v_minicroft(skill_ids=[SKILL_ID], lang=LANG)
    _PIPE = _MC.intents.pipeline_plugins["ovos-m2v-pipeline"]
    _PIPE._ensure_model(background_ok=False)


def tearDownModule():
    global _MC, _XDG, _ORIG_XDG
    if _MC is not None:
        _MC.stop()
        _MC = None
    if _ORIG_XDG is None:
        os.environ.pop("XDG_DATA_HOME", None)
    else:
        os.environ["XDG_DATA_HOME"] = _ORIG_XDG
    if _XDG is not None:
        shutil.rmtree(_XDG, ignore_errors=True)
        _XDG = None


class TestM2VNumberFactsGoldenEffect(unittest.TestCase):
    """Effect assertions: golden utterance in -> correct intent -> stubbed fact spoken."""

    def _run(self, utterance: str, lang: str = LANG, timeout: float = 15.0):
        speaks = []
        failures = []

        def _on_speak(msg):
            speaks.append(msg)

        def _on_fail(msg):
            failures.append(msg)

        _MC.bus.on("speak", _on_speak)
        _MC.bus.on("complete_intent_failure", _on_fail)
        sess = Session(session_id=f"m2v-golden-{hash(utterance)}", pipeline=M2V_PIPELINE)
        sess.lang = lang
        try:
            _MC.bus.emit(Message(
                "recognizer_loop:utterance",
                data={"utterances": [utterance], "lang": lang},
                context={"session": sess.serialize(), "lang": lang},
            ))
            import time as _t
            deadline = _t.time() + timeout
            while _t.time() < deadline and not speaks and not failures:
                _t.sleep(0.05)
        finally:
            _MC.bus.remove("speak", _on_speak)
            _MC.bus.remove("complete_intent_failure", _on_fail)

        if not speaks:
            return None, bool(failures)
        return (speaks[0].data.get("utterance") or ""), False

    def _assert_effect(self, utterance, expected_fact):
        text, failed = self._run(utterance)
        self.assertFalse(failed, f"{utterance!r} did not route: complete_intent_failure")
        self.assertIsNotNone(text, f"{utterance!r} produced no spoken output")
        self.assertEqual(
            text, expected_fact,
            f"{utterance!r} spoke {text!r}, expected the stubbed fact {expected_fact!r}")

    def test_give_me_a_fact_about_the_number_42(self):
        self._assert_effect("give me a fact about the number 42", "NUMBER_FACT")

    def test_tell_me_a_random_number_fact(self):
        self._assert_effect("tell me a random number fact", "NUMBER_FACT")

    def test_give_me_a_math_fact(self):
        self._assert_effect("give me a math fact", "MATH_FACT")

    def test_fact_about_today(self):
        self._assert_effect("fact about today", "DATE_FACT")

    def test_fact_about_the_year_1992(self):
        self._assert_effect("fact about the year 1992", "YEAR_FACT")


class TestM2VRegisteredLabelRouting(unittest.TestCase):
    """The model's labels carry the skill's real runtime id and route it."""

    def test_registered_skill_id_labels_route(self):
        classes = {str(c) for c in _PIPE.model.classes_}
        registered = set(_PIPE.intents)
        self.assertIn(f"{SKILL_ID}:number_trivia", registered)
        self.assertTrue(
            registered & classes,
            "registered intent labels do not intersect the model's classes; "
            f"{SKILL_ID} would route nothing through this model")


if __name__ == "__main__":
    unittest.main()
