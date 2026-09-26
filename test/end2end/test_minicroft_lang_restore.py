"""A MiniCroft restores the `lang` it saved, so the stop order matters.

`MiniCroft.__init__` records the `lang` that is current at construction and
writes that value back on stop. When several crofts are alive at once the
saves nest like a stack: the first holds the process default, the second
holds the first's language, and so on. Stopping them in creation order
unwinds that stack backwards, and the last stop leaves the process on a
foreign locale.

Nothing in the module that did this fails when it happens. The next test
file in the same xdist worker fails instead, which is what made `#105`'s
ovoscope job red: twelve failures in `test_intent_files_padacioso.py` and
`test_intents_en_us.py`, neither of which had changed.

This pins the ordering itself, so the class is caught here rather than as a
cross-file mystery.
"""
import pytest
from ovos_bus_client.session import SessionManager
from ovoscope import get_minicroft

SKILL_ID = "ovos-skill-number-facts.openvoiceos"
PIPELINE = ["ovos-padatious-pipeline-plugin-high",
            "ovos-adapt-pipeline-plugin-high"]


def _boot(lang):
    return get_minicroft([SKILL_ID], max_wait=150, lang=lang,
                         default_pipeline=PIPELINE)


def _lang_after_stopping(reverse):
    """Boot three crofts in different languages, stop them, report the lang."""
    original = SessionManager.default_session.lang
    # Three languages, none of them the process default. With only two, and
    # the first of them equal to the default, creation order happens to end
    # on the right value and the defect is invisible: the run that proved
    # this test needed a third croft.
    crofts = [_boot("it-IT"), _boot("nl-NL"), _boot("pt-PT")]
    try:
        for mc in (reversed(crofts) if reverse else iter(crofts)):
            mc.stop()
        return original, SessionManager.default_session.lang
    finally:
        for mc in crofts:
            try:
                mc.stop()
            except Exception:
                pass
        SessionManager.default_session.lang = original


def test_reverse_order_restores_the_original_lang():
    original, after = _lang_after_stopping(reverse=True)
    assert after == original, (
        f"stopping in reverse creation order must restore {original!r}, "
        f"the process left on {after!r}"
    )


def test_creation_order_does_not_restore_it():
    """The control for the test above.

    Without this, a single-croft case would pass either way and the first
    test would prove nothing about the order. This records the defect the
    fixture in `test_golden_utterances_multilang.py` had: the last stop
    writes back the language the SECOND croft saved, which is the first
    croft's, not the process default.
    """
    original, after = _lang_after_stopping(reverse=False)
    assert after != original, (
        "creation order is expected to leave a foreign lang; if this now "
        "restores correctly, ovoscope changed how it saves lang and the "
        "reverse-order requirement should be re-read rather than assumed"
    )
