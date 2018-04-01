from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util.parse import extractnumber, extract_datetime
import sys
if sys.version_info[0] < 3:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen


def year_trivia(n):
    return urlopen('http://numbersapi.com/%d/trivia' % n).read()


def number_trivia(n):
    return urlopen('http://numbersapi.com/%d/trivia' % n).read()


def number_math(n):
    return urlopen('http://numbersapi.com/%d/math' % n).read()


def date_trivia(month, day):
    return urlopen(
            'http://numbersapi.com/%d/%d/date' % (month, day)).read()


def random_trivia():
    return urlopen('http://numbersapi.com/random/trivia').read()


def random_math():
    return urlopen('http://numbersapi.com/random/math').read()


def random_year():
    return urlopen('http://numbersapi.com/random/year').read()


def random_date():
    return urlopen('http://numbersapi.com/random/date').read()


class NumbersSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_handler(IntentBuilder("number_trivia").require(
        'Numbers').require("fact").optionally("api").optionally("random"))
    def handle_numbers(self, message):
        random = message.data.get("random", False)
        number = None
        if not random:
            remainder = message.utterance_remainder()
            lang = message.data.get("lang", self.lang)
            number = extractnumber(remainder, lang)
        if number is not None:
            self.speak(number_trivia(number))
        else:
            self.speak(random_trivia())

    @intent_handler(IntentBuilder("math_trivia").require(
        'math').require("fact").optionally("api").optionally(
        "random").optionally("number"))
    def handle_math(self, message):
        random = message.data.get("random", False)
        number = None
        if not random:
            remainder = message.utterance_remainder()
            lang = message.data.get("lang", self.lang)
            number = extractnumber(remainder, lang)
        if number:
            self.speak(number_math(number))
        else:
            self.speak(random_math())

    @intent_handler(IntentBuilder("date_trivia").require(
        'date_indicator').require("fact").optionally("api")
        .optionally("random"))
    def handle_date(self, message):
        random = message.data.get("random", False)
        date = None
        if not random:
            remainder = message.data["utterance"]
            lang = message.data.get("lang", self.lang)
            date = extract_datetime(remainder, lang=lang)
            self.log.info("extracted date: " + str(date[0]))
            self.log.info("utterance remainder: " + str(date[1]))
            date = date[0]

        if date:
            self.speak(date_trivia(date.month, date.day))
        else:
            self.speak(random_date())

    @intent_handler(IntentBuilder("year_trivia").require(
        'year').require("fact").optionally("api").optionally("random"))
    def handle_year(self, message):
        random = message.data.get("random", False)
        number = None
        if not random:
            remainder = message.utterance_remainder()
            lang = message.data.get("lang", self.lang)
            number = extractnumber(remainder, lang)

        if number:
            self.speak(year_trivia(number))
        else:
            self.speak(random_year())


def create_skill():
    return NumbersSkill()

