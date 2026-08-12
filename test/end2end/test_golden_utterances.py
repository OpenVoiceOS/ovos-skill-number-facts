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
from ovoscope import CaptureSession, get_minicroft, ADAPT_PIPELINE  # noqa: E402

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


def _candidates(skill_id: str, intent_label: str) -> set:
    """padatious/padacioso plugin versions register the matched-intent bus
    event under different normalizations of the ``.intent`` filename
    basename -- candidates cover both the suffixed and unsuffixed forms.
    Adapt intent names (eg. "number_trivia") have no ``.intent`` suffix
    to strip."""
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
    session.pipeline = ADAPT_PIPELINE
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
