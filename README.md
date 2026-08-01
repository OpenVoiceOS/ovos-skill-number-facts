# Numbers

An [OVOS](https://github.com/OpenVoiceOS) skill that reads facts about numbers. It also covers math, years, and dates. It gets the facts from [numbersapi.com](http://numbersapi.com).

## Install

```bash
pip install ovos-skill-number-facts
```

## Usage

Say any of these phrases to the assistant.

Random facts:

* "random math fact"
* "random number trivia"
* "random date curiosity"
* "random year trivia"

Facts about a number, date, or year you name:

* "fact about number 666"
* "math fact about number 5"
* "curiosity about year 1992"
* "trivia about tomorrow"
* "trivia about next week"
* "fact about yesterday"
* "curiosity about march 13"

The skill extracts the number, date, or year from your request. If it finds none, it asks numbersapi.com for a random fact instead.

## Related projects

* [OpenVoiceOS/ovos-workshop](https://github.com/OpenVoiceOS/ovos-workshop): the skill framework this skill runs on
* [OpenVoiceOS/ovos-date-parser](https://github.com/OpenVoiceOS/ovos-date-parser): extracts dates from an utterance
* [OpenVoiceOS/ovos-number-parser](https://github.com/OpenVoiceOS/ovos-number-parser): extracts numbers from an utterance

## Credits

[JarbasAI](https://github.com/JarbasAl)

## License

[Apache-2.0](LICENSE)
