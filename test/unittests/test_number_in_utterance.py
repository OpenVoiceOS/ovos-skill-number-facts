"""The fact is about the number the user said, not the article before it."""
from unittest.mock import patch

import ovos_skill_number_facts as _skill_module
import pytest
from ovos_bus_client.message import Message
from ovos_skill_number_facts import NumbersSkill
from ovos_utils.fakebus import FakeBus

SKILL_ID = "ovos-skill-number-facts.openvoiceos"


class LocalizedSkill(NumbersSkill):
    lang = None


def ask(handler, lang, utterance):
    skill = LocalizedSkill()
    skill._startup(FakeBus(), SKILL_ID)
    skill.lang = lang
    spoken, numbers = [], []
    skill.speak = lambda *a, **k: spoken.append(a[0])
    skill.speak_dialog = lambda *a, **k: spoken.append(a[0])

    def fact(n):
        numbers.append(n)
        return "NUMBER_FACT"

    with patch.object(_skill_module, "number_trivia", fact), \
            patch.object(_skill_module, "number_math", fact), \
            patch.object(_skill_module, "random_trivia", lambda: "RANDOM_FACT"), \
            patch.object(_skill_module, "random_math", lambda: "RANDOM_FACT"):
        getattr(skill, handler)(Message("", {"utterance": utterance}))
    return numbers, spoken


@pytest.mark.parametrize("lang, utterance, number", [
    ("en-US", "number fact a dozen", 12),
    ("pt-PT", "conta-me uma curiosidade sobre o número sete", 7),
    ("pt-PT", "diz-me um facto sobre o número quarenta e dois", 42),
    ("pt-BR", "me conta uma curiosidade sobre o número sete", 7),
    ("es-ES", "dime una curiosidad sobre el número siete", 7),
    ("fr-FR", "raconte-moi une anecdote sur le nombre sept", 7),
    ("it-IT", "raccontami una curiosità sul numero sette", 7),
    ("ca-ES", "digues-me una curiositat sobre el número set", 7),
    ("gl-ES", "dime unha curiosidade sobre o número sete", 7),
    ("oc-FR", "conta-me una curiositat sul numèro sèt", 7),
    ("de-DE", "nenne mir eine Tatsache über die Zahl sieben", 7),
    ("nl-NL", "weet jij een feitje over het getal zeven", 7),
    ("sv-SE", "ge mig ett slumpmässigt fakta om numret sju", 7),
    ("fa-IR", "یک واقعیت درباره عدد هفت بگو", 7),
])
def test_trivia_is_about_the_spoken_number(lang, utterance, number):
    numbers, spoken = ask("handle_numbers", lang, utterance)
    assert (numbers, spoken) == ([number], ["NUMBER_FACT"])


@pytest.mark.parametrize("utterance", [
    "give me a math fact about a dozen",
    # "second" is also a unit of time, so it reads below "a dozen"
    "give me a second math fact about a dozen",
])
def test_math_fact_is_about_the_spoken_number(utterance):
    numbers, spoken = ask("handle_math", "en-US", utterance)
    assert (numbers, spoken) == ([12], ["NUMBER_FACT"])


@pytest.mark.parametrize("utterance", [
    "diz-me uma curiosidade sobre os números",
    "dá-me um facto sobre os números",
])
def test_an_article_alone_is_no_number(utterance):
    numbers, spoken = ask("handle_numbers", "pt-PT", utterance)
    assert (numbers, spoken) == ([], ["no_number_found", "RANDOM_FACT"])
