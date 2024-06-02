from urllib.request import urlopen

from lingua_franca.parse import extract_datetime
from lingua_franca.parse import extract_number
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
from ovos_workshop.skills import OVOSSkill


def year_trivia(n):
    return urlopen('http://numbersapi.com/%d/trivia' % n).read().decode("utf-8")


def number_trivia(n):
    return urlopen('http://numbersapi.com/%d/trivia' % n).read().decode("utf-8")


def number_math(n):
    return urlopen('http://numbersapi.com/%d/math' % n).read().decode("utf-8")


def date_trivia(month, day):
    return urlopen('http://numbersapi.com/%d/%d/date' % (month, day)).read().decode("utf-8")


def random_trivia():
    return urlopen('http://numbersapi.com/random/trivia').read().decode("utf-8")


def random_math():
    return urlopen('http://numbersapi.com/random/math').read().decode("utf-8")


def random_year():
    return urlopen('http://numbersapi.com/random/year').read().decode("utf-8")


def random_date():
    return urlopen('http://numbersapi.com/random/date').read().decode("utf-8")


class NumbersSkill(OVOSSkill):

    @intent_handler(
        IntentBuilder("number_trivia").require('Numbers').require(
            "fact").optionally("api").optionally("random"))
    def handle_numbers(self, message):
        random = message.data.get("random")
        number = None
        if not random:
            number = extract_number(message.data["utterance"], lang=self.lang)
        if number is not None:
            self.speak(number_trivia(number))
        else:
            self.speak(random_trivia())

    @intent_handler(
        IntentBuilder("math_trivia").require('math').require("fact").
        optionally("api").optionally("random").optionally("number"))
    def handle_math(self, message):
        random = message.data.get("random")
        number = None
        if not random:
            number = extract_number(message.data["utterance"], lang=self.lang)
        if number:
            self.speak(number_math(number))
        else:
            self.speak(random_math())

    @intent_handler(
        IntentBuilder("date_trivia").require('date_indicator').require(
            "fact").optionally("api").optionally("random"))
    def handle_date(self, message):
        random = message.data.get("random")
        date = None
        if not random:
            date = extract_datetime(message.data["utterance"], lang=self.lang)
            self.log.info("extracted date: " + str(date[0]))
            self.log.info("utterance remainder: " + str(date[1]))
            date = date[0]

        if date:
            self.speak(date_trivia(date.month, date.day))
        else:
            self.speak(random_date())

    @intent_handler(
        IntentBuilder("year_trivia").require('year').require(
            "fact").optionally("api").optionally("random"))
    def handle_year(self, message):
        random = message.data.get("random")
        number = None
        if not random:
            number = extract_number(message.data["utterance"], lang=self.lang)

        if number:
            self.speak(year_trivia(number))
        else:
            self.speak(random_year())


if __name__ == "__main__":
    from ovos_utils.fakebus import FakeBus
    from ovos_bus_client.message import Message


    # print speak for debugging
    def spk(utt, *args, **kwargs):
        print(utt)


    s = NumbersSkill(skill_id="fake.test", bus=FakeBus())
    s.speak = spk

    s.handle_year(Message("", {"random": True}))
    s.handle_date(Message("", {"random": True}))
    s.handle_math(Message("", {"random": True}))
    s.handle_numbers(Message("", {"random": True}))
