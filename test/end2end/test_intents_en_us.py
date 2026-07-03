"""End-to-end intent-routing tests for ovos-skill-number-facts (en-US).

These assert *per-utterance* that the Adapt pipeline routes an utterance to the
right trivia handler and that the skill speaks the fact back. They deliberately
use subset assertions over the captured message stream rather than a strict
full-sequence match: the exact ordered sequence drifts across ovos-core /
ovoscope releases (e.g. an extra ``ovos.intent.matched`` message, or ``speak``
vs ``ovos.utterance.speak``), which is orthogonal to what this skill is
responsible for.

The skill fetches facts from ``numbersapi.com`` over the network. The suite
patches those module-level fetchers with deterministic stubs *before* the
MiniCroft loads the skill, so the tests exercise pure intent routing without a
network dependency and stay fast and reproducible.

Run:
    uv run pytest test/end2end/ -v
"""
from unittest import TestCase

import ovos_skill_number_facts as _skill_module

# Deterministic, network-free fact fetchers. Each category returns a distinct
# sentinel so the spoken-response assertions can tell the handlers apart.
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
from ovoscope import get_minicroft, CaptureSession, ADAPT_PIPELINE  # noqa: E402

SKILL_ID = "ovos-skill-number-facts.openvoiceos"
LANG = "en-US"


def _session(tag: str) -> Session:
    session = Session(f"e2e-en_us-numfacts-{tag}")
    session.lang = LANG
    session.pipeline = ADAPT_PIPELINE
    return session


def _utterance(utt: str, session: Session) -> Message:
    return Message(
        "recognizer_loop:utterance",
        {"utterances": [utt], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )


class _TriviaRoutingMixin:
    """Shared MiniCroft wiring for the number-facts skill."""

    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

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
        self.assertIn(
            intent, types,
            f"expected {intent!r} to be matched for {utterance!r}, "
            f"got {types}",
        )
        spoken = self._spoken(messages)
        self.assertTrue(
            any(sentinel in utt for utt in spoken),
            f"expected a spoken response containing {sentinel!r} for "
            f"{utterance!r}, got {spoken}",
        )


class TestNumberTrivia(_TriviaRoutingMixin, TestCase):
    """number_trivia routing across phrasings."""

    def test_number_fact(self):
        self.assertRoutesTo("tell me a number fact", "number_trivia", "NUMBER_FACT")

    def test_random_number_fact(self):
        self.assertRoutesTo("random number fact", "number_trivia", "NUMBER_FACT")


class TestMathTrivia(_TriviaRoutingMixin, TestCase):
    """math_trivia routing."""

    def test_math_fact(self):
        self.assertRoutesTo("give me a math fact", "math_trivia", "MATH_FACT")


class TestDateTrivia(_TriviaRoutingMixin, TestCase):
    """date_trivia routing."""

    def test_date_fact(self):
        self.assertRoutesTo("fact about december", "date_trivia", "DATE_FACT")


class TestYearTrivia(_TriviaRoutingMixin, TestCase):
    """year_trivia routing."""

    def test_year_fact(self):
        self.assertRoutesTo("fact about the year 1992", "year_trivia", "YEAR_FACT")
