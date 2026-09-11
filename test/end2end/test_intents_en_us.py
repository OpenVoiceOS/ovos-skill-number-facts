"""End-to-end intent-routing tests for ovos-skill-number-facts (en-US).

These assert *per-utterance* that the padacioso (``.intent`` file) pipeline
routes an utterance to the right trivia handler and that the skill speaks the
fact back. They deliberately
use subset assertions over the captured message stream rather than a strict
full-sequence match: the exact ordered sequence drifts across ovos-core /
ovoscope releases (e.g. an extra ``ovos.intent.matched`` message, or ``speak``
vs ``ovos.utterance.speak``), which is orthogonal to what this skill is
responsible for.

The skill fetches facts from ``numbersapi.com`` over the network. The suite
patches those module-level fetchers with deterministic stubs *before* the
MiniCroft loads the skill, so the tests exercise pure intent routing without a
network dependency and stay fast and reproducible.

Beyond routing, these tests assert the *effect*: the spoken line must be one
the handler could actually have produced for that branch. The
``no.number.found`` recovery path is checked against the lines shipped in
``locale/en-US/no.number.found.dialog``, read from disk at test time rather
than restated in the test, and that set is asserted disjoint from the fetch
sentinels so a handler that speaks the wrong line cannot pass by accident.
A stubbed fetch failure is asserted to reach some spoken recovery and never
a fabricated fact; see ``TestFetchFailureRecovery`` for why the exact wording
of that recovery line is deliberately left unchecked.

Run:
    uv run pytest test/end2end/ -v
"""
from pathlib import Path
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
from ovoscope import get_minicroft, CaptureSession, PADACIOSO_PIPELINE  # noqa: E402

SKILL_ID = "ovos-skill-number-facts.openvoiceos"
LANG = "en-US"
LOCALE_EN_US = Path(__file__).parent.parent.parent / "locale" / "en-US"


def _dialog_lines(name: str) -> set:
    path = LOCALE_EN_US / f"{name}.dialog"
    with open(path, encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


# Read once, directly from the shipped dialog file -- never from a captured
# bus message -- so this set is independent of the code under test.
NO_NUMBER_FOUND_LINES = _dialog_lines("no.number.found")

# The recovery-path dialog must not share a line with any fact sentinel, or a
# handler that speaks the wrong one would still pass membership checks below.
for _sentinel in set(_STUBS.values()):
    assert not (NO_NUMBER_FOUND_LINES & {_sentinel}), (
        f"no.number.found.dialog must be disjoint from fetch sentinel "
        f"{_sentinel!r}, got overlap"
    )


def _session(tag: str) -> Session:
    session = Session(f"e2e-en_us-numfacts-{tag}")
    session.lang = LANG
    session.pipeline = PADACIOSO_PIPELINE
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

    def test_give_me_a_fact_about_numbers(self):
        self.assertRoutesTo("give me a fact about numbers", "number_trivia", "NUMBER_FACT")

    def test_no_number_speaks_no_number_found_dialog(self):
        """An utterance with no extractable number must speak a line drawn
        from ``no.number.found.dialog`` on the way to the random fallback,
        not merely any spoken response."""
        messages = self._capture("give me a fact about numbers")
        spoken = self._spoken(messages)
        self.assertTrue(
            any(utt in NO_NUMBER_FOUND_LINES for utt in spoken),
            f"expected one of no.number.found.dialog's own lines to be "
            f"spoken, got {spoken!r}",
        )

    def test_number_given_skips_no_number_found_dialog(self):
        """When a number is present in the utterance, the recovery dialog
        for a *missing* number must never be spoken."""
        messages = self._capture("number fact 7")
        spoken = self._spoken(messages)
        self.assertFalse(
            any(utt in NO_NUMBER_FOUND_LINES for utt in spoken),
            f"no.number.found.dialog must not be spoken when a number was "
            f"found, got {spoken!r}",
        )


class TestMathTrivia(_TriviaRoutingMixin, TestCase):
    """math_trivia routing."""

    def test_math_fact(self):
        self.assertRoutesTo("give me a math fact", "math_trivia", "MATH_FACT")


class TestDateTrivia(_TriviaRoutingMixin, TestCase):
    """date_trivia routing."""

    def test_date_fact(self):
        self.assertRoutesTo("fact about december 3", "date_trivia", "DATE_FACT")


class TestYearTrivia(_TriviaRoutingMixin, TestCase):
    """year_trivia routing."""

    def test_year_fact(self):
        self.assertRoutesTo("fact about the year 1992", "year_trivia", "YEAR_FACT")


class TestFetchFailureRecovery(TestCase):
    """The skill must recover from a failed ``numbersapi.com`` fetch by
    speaking something, never by staying silent, and never by speaking a
    fact it never received. The exact wording of that recovery line is
    deliberately not asserted here: ``ovos_workshop`` speaks the bare
    ``skill.error`` resource identifier when a skill ships no
    ``skill.error.dialog``, and no skill in the fleet ships one, so pinning
    a wording in this suite would either encode that fleet-wide gap as
    correct or require a fix that belongs in ``ovos_workshop``, not here.

    ``number_trivia`` is stubbed to raise instead of return a sentinel, for
    this class only, so the failure is exercised without touching the
    network.
    """

    @classmethod
    def setUpClass(cls):
        cls._original_number_trivia = _skill_module.number_trivia

        def _raise(*_args, **_kwargs):
            raise RuntimeError("numbersapi.com unreachable")

        _skill_module.number_trivia = _raise
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "minicroft", None):
            cls.minicroft.stop()
        _skill_module.number_trivia = cls._original_number_trivia

    def test_fetch_failure_speaks_error_not_a_fact(self):
        session = _session("fetch-failure")
        capture = CaptureSession(self.minicroft)
        capture.capture(_utterance("number fact 7", session), timeout=30)
        messages = capture.finish()

        spoken = [
            m.data.get("utterance", "")
            for m in messages
            if m.msg_type in ("speak", "ovos.utterance.speak")
        ]
        self.assertTrue(spoken, "expected a spoken response after the fetch failed")
        self.assertFalse(
            any("NUMBER_FACT" in utt for utt in spoken),
            f"a failed fetch must never speak a fact, got {spoken!r}",
        )
