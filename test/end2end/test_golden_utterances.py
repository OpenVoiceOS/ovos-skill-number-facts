"""Golden-utterance end-to-end coverage for ovos-skill-number-facts (en-US).

The golden corpus (``golden_utterances.jsonl``) is a vendored slice of the
shared ovoscope golden-utterance dataset, keyed by
``skill_id == "ovos-skill-number-facts.openvoiceos"``. One shared
``MiniCroft`` (module-scoped fixture) is booted for the whole suite.

The skill fetches facts from ``numbersapi.com`` over the network; the
module-level fetchers are patched with deterministic stubs *before*
MiniCroft loads the skill (same technique as ``test_intents_en_us.py``) so
the suite stays fast, reproducible, and network-free.
"""
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


import json  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from ovos_bus_client.message import Message  # noqa: E402
from ovos_bus_client.session import Session  # noqa: E402
from ovoscope import CaptureSession, get_minicroft, PADACIOSO_PIPELINE  # noqa: E402

SKILL_ID = "ovos-skill-number-facts.openvoiceos"
LANG = "en-US"

GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"

# utterances lifted verbatim from OTHER skills' golden-utterance slices,
# picked for lexical overlap with number-facts' "number"/"math"/"date"/
# "year"/"random" vocabulary.
NEGATIVE_UTTERANCES = [
    ("what's the weather", "ovos-skill-weather.openvoiceos"),
    ("set a timer for 5 minutes", "ovos-skill-alerts.openvoiceos"),
    ("play some music", "ovos-skill-music.openvoiceos"),
    ("what's today's date", "ovos-skill-date-time.openvoiceos"),
    ("what year is it", "ovos-skill-date-time.openvoiceos"),
    ("tell me a random joke", "ovos-skill-icanhazdadjokes.openvoiceos"),
    ("play a random song", "ovos-skill-music.openvoiceos"),
]

# sibling-confusion negatives: utterances that should be claimed by ONE
# specific trivia intent of this skill and must NOT also be claimed by any
# of its siblings (e.g. a math request should never fall into number_trivia,
# a year request should never fall into date_trivia, etc).
SIBLING_NEGATIVES = [
    # (utterance, correct_label, wrong_labels)
    ("give me a math fact", "math_trivia", ["number_trivia", "date_trivia", "year_trivia"]),
    ("fact about the year 1992", "year_trivia", ["number_trivia", "math_trivia", "date_trivia"]),
    ("fact about december 3", "date_trivia", ["number_trivia", "math_trivia", "year_trivia"]),
    ("number fact 7", "number_trivia", ["math_trivia", "date_trivia", "year_trivia"]),
    ("tell me a year fact", "year_trivia", ["number_trivia", "math_trivia", "date_trivia"]),
    ("tell me a date fact", "date_trivia", ["number_trivia", "math_trivia", "year_trivia"]),
]


def _candidates(skill_id: str, intent_label: str) -> set:
    """padatious/padacioso plugin versions register the matched-intent bus
    event under different normalizations of the ``.intent`` filename
    basename -- candidates cover both the suffixed and unsuffixed forms.
    Plain intent names (eg. a legacy Adapt registration) have no ``.intent``
    suffix to strip."""
    base = intent_label[:-len(".intent")] if intent_label.endswith(".intent") else intent_label
    return {f"{skill_id}:{intent_label}", f"{skill_id}:{base}"}


def _load_golden_rows():
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


GOLDEN_ROWS = [pytest.param(r, id=r["utterance"]) for r in _load_golden_rows()]


@pytest.fixture(scope="module")
def minicroft():
    mc = get_minicroft([SKILL_ID])
    yield mc
    mc.stop()


def _types(mc, text, session_id):
    session = Session(session_id)
    session.lang = LANG
    session.pipeline = PADACIOSO_PIPELINE
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc)
    capture.capture(utterance, timeout=30)
    return [m.msg_type for m in capture.finish()]


def _golden_id(row):
    return row["utterance"]


@pytest.mark.timeout(60)
@pytest.mark.parametrize("row", GOLDEN_ROWS, ids=_golden_id)
def test_golden_utterance(minicroft, row):
    candidates = _candidates(SKILL_ID, row["intent_label"])
    types = _types(minicroft, row["utterance"], f"golden-{_golden_id(row)}")
    assert any(t in candidates for t in types), (
        f"{row['utterance']!r}: expected one of {sorted(candidates)!r}, got {types!r}"
    )


@pytest.mark.timeout(60)
@pytest.mark.parametrize("negative", NEGATIVE_UTTERANCES, ids=lambda n: n[0])
def test_negative_confusable_not_claimed(minicroft, negative):
    text, source_skill = negative
    types = _types(minicroft, text, f"negative-{text}")
    claimed = any(t.startswith(f"{SKILL_ID}:") for t in types)
    assert not claimed, f"{text!r} (from {source_skill}) was incorrectly claimed by {SKILL_ID}"


@pytest.mark.timeout(60)
@pytest.mark.parametrize("case", SIBLING_NEGATIVES, ids=lambda c: c[0])
def test_sibling_intent_not_confused(minicroft, case):
    """A trivia utterance must route to exactly its own intent, never to one
    of the skill's other three trivia intents (e.g. a year request must not
    be claimed by number_trivia/math_trivia/date_trivia)."""
    text, correct_label, wrong_labels = case
    types = _types(minicroft, text, f"sibling-{text}")
    correct = _candidates(SKILL_ID, correct_label)
    assert any(t in correct for t in types), (
        f"{text!r}: expected one of {sorted(correct)!r}, got {types!r}"
    )
    for wrong_label in wrong_labels:
        wrong = _candidates(SKILL_ID, wrong_label)
        assert not any(t in wrong for t in types), (
            f"{text!r}: incorrectly also claimed by sibling intent {wrong_label!r} ({types!r})"
        )


@pytest.mark.timeout(60)
@pytest.mark.parametrize(
    "utterance,handler_name,number",
    [
        ("give me a fact about the number 42", "number_trivia", "42"),
        ("give me a trivia about the number 256", "number_trivia", "256"),
        ("tell me a curiosity about number 15", "number_trivia", "15"),
        ("number fact 7", "number_trivia", "7"),
        ("give me a math fact about the number 7", "number_math", "7"),
        ("tell me a math trivia about 12", "number_math", "12"),
        ("fact about the year 1992", "year_trivia", "1992"),
        ("year fact 2001", "year_trivia", "2001"),
        ("tell me a fact about the year 2020", "year_trivia", "2020"),
    ],
    ids=lambda v: v if isinstance(v, str) else None,
)
def test_number_slot_is_actually_extracted(minicroft, utterance, handler_name, number):
    """Prove the {number}/{year} slot text is not just matched by the
    template but actually reaches the fact-fetcher with the right value --
    a template that matches the intent but drops/garbles the slot is just as
    broken as one that never matches at all."""
    original = getattr(_skill_module, handler_name)
    captured = []

    def _echo(n):
        captured.append(n)
        return f"ECHO:{n}"

    setattr(_skill_module, handler_name, _echo)
    try:
        session = Session(f"slot-{utterance}")
        session.lang = LANG
        session.pipeline = PADACIOSO_PIPELINE
        msg = Message(
            "recognizer_loop:utterance",
            {"utterances": [utterance], "lang": LANG},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )
        capture = CaptureSession(minicroft)
        capture.capture(msg, timeout=30)
        messages = capture.finish()
    finally:
        setattr(_skill_module, handler_name, original)

    spoken = [m.data.get("utterance", "") for m in messages if m.msg_type in ("speak", "ovos.utterance.speak")]
    assert captured, f"{utterance!r}: fact-fetcher {handler_name!r} was never called (number not extracted)"
    assert str(captured[0]) == str(int(number)) or str(captured[0]) == number, (
        f"{utterance!r}: expected extracted number {number!r}, got {captured!r}"
    )
    assert any(f"ECHO:{captured[0]}" in utt for utt in spoken), (
        f"{utterance!r}: extracted number {captured[0]!r} did not reach the spoken response ({spoken!r})"
    )


@pytest.mark.timeout(60)
def test_date_slot_is_actually_extracted(minicroft):
    """Same slot-extraction proof as above, for the two-argument date_trivia
    fetcher ({date} + explicit month)."""
    original = _skill_module.date_trivia
    captured = []

    def _echo(month, day):
        captured.append((month, day))
        return f"ECHO:{month}:{day}"

    setattr(_skill_module, "date_trivia", _echo)
    try:
        session = Session("slot-date-trivia")
        session.lang = LANG
        session.pipeline = PADACIOSO_PIPELINE
        msg = Message(
            "recognizer_loop:utterance",
            {"utterances": ["fact about december 3"], "lang": LANG},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )
        capture = CaptureSession(minicroft)
        capture.capture(msg, timeout=30)
        messages = capture.finish()
    finally:
        setattr(_skill_module, "date_trivia", original)

    spoken = [m.data.get("utterance", "") for m in messages if m.msg_type in ("speak", "ovos.utterance.speak")]
    assert captured == [(12, 3)], f"expected month=12 day=3 to be extracted, got {captured!r}"
    assert any("ECHO:12:3" in utt for utt in spoken)
