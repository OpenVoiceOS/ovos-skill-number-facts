"""Each trivia intent routes from its ``.intent`` file, with no Adapt stage
in the pipeline, and the skill speaks its fact."""
from unittest import TestCase

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
from ovoscope import CaptureSession  # noqa: E402
from ovoscope.routing import PIPELINE, TALLY, get_prototype_minicroft  # noqa: E402

SKILL_ID = "ovos-skill-number-facts.openvoiceos"
LANG = "en-US"


def _session(tag: str) -> Session:
    session = Session(f"e2e-adaptless-numfacts-{tag}")
    session.lang = LANG
    session.pipeline = list(PIPELINE)
    return session


def _utterance(utt: str, session: Session) -> Message:
    return Message(
        "recognizer_loop:utterance",
        {"utterances": [utt], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )


class TestTriviaRoutingWithoutAdapt(TestCase):
    """Adapt-less pipeline coverage for the four trivia intents."""

    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_prototype_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()

    def _capture(self, utterance: str):
        session = _session(str(hash(utterance)))
        capture = CaptureSession(self.minicroft)
        capture.capture(_utterance(utterance, session), timeout=30)
        return capture.finish()

    def _spoken(self, messages):
        return [
            m.data.get("utterance", "")
            for m in messages
            if m.msg_type in ("speak", "ovos.utterance.speak")
        ]

    def assertRoutesTo(self, utterance: str, intent_label: str, sentinel: str):
        intent = f"{SKILL_ID}:{intent_label}"
        messages = self._capture(utterance)
        types = [m.msg_type for m in messages]
        TALLY.assert_routed(utterance, intent, types)
        spoken = self._spoken(messages)
        self.assertTrue(
            any(sentinel in utt for utt in spoken),
            f"expected a spoken response containing {sentinel!r} for "
            f"{utterance!r}, got {spoken}",
        )

    def test_number_fact(self):
        self.assertRoutesTo(
            "give me a fact about the number 42", "number_trivia", "NUMBER_FACT")

    def test_math_fact(self):
        self.assertRoutesTo("give me a math fact", "math_trivia", "MATH_FACT")

    def test_date_fact(self):
        self.assertRoutesTo("fact about today", "date_trivia", "DATE_FACT")

    def test_year_fact(self):
        self.assertRoutesTo(
            "fact about the year 1969", "year_trivia", "YEAR_FACT")
