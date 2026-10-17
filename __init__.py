from urllib.request import urlopen

from ovos_number_parser import extract_number
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill


def number_trivia(n):
    return urlopen('http://numbersapi.com/%d/trivia' % n).read().decode("utf-8")


def number_math(n):
    return urlopen('http://numbersapi.com/%d/math' % n).read().decode("utf-8")


def random_trivia():
    return urlopen('http://numbersapi.com/random/trivia').read().decode("utf-8")


def random_math():
    return urlopen('http://numbersapi.com/random/math').read().decode("utf-8")


class NumbersSkill(OVOSSkill):

    @intent_handler("number_trivia.intent")
    def handle_numbers(self, message):
        random = message.data.get("random")
        number = None
        if not random:
            number = extract_number(message.data["utterance"], lang=self.lang)
        if number is not None and number is not False:
            self.speak(number_trivia(number))
        else:
            if not random:
                self.speak_dialog("no_number_found")
            self.speak(random_trivia())

    @intent_handler("math_trivia.intent")
    def handle_math(self, message):
        random = message.data.get("random")
        number = None
        if not random:
            number = extract_number(message.data["utterance"], lang=self.lang)
        if number is not None and number is not False:
            self.speak(number_math(number))
        else:
            self.speak(random_math())



if __name__ == "__main__":
    from ovos_utils.fakebus import FakeBus
    from ovos_bus_client.message import Message

    # print speak for debugging
    def spk(utt, *args, **kwargs):
        print(utt)


    s = NumbersSkill(skill_id="fake.test", bus=FakeBus())
    s.speak = spk

    s.handle_math(Message("", {"random": True}))
    s.handle_numbers(Message("", {"utterance": "fact about number six hundred sixty six"}))
