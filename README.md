# Numbers

An [OVOS](https://github.com/OpenVoiceOS) skill that reads facts about numbers. It also covers math. It gets the facts from [numbersapi.com](http://numbersapi.com).

## Install

```bash
pip install ovos-skill-number-facts
```

## Usage

Say any of these phrases to the assistant.

Random facts:

* "random math fact"
* "random number trivia"

Facts about a number you name:

* "fact about number 666"
* "math fact about number 5"

The skill extracts the number from your request. If it finds none, it asks numbersapi.com for a random fact instead.

## Related projects

* [OpenVoiceOS/ovos-workshop](https://github.com/OpenVoiceOS/ovos-workshop): the skill framework this skill runs on
* [OpenVoiceOS/ovos-number-parser](https://github.com/OpenVoiceOS/ovos-number-parser): extracts numbers from an utterance

## Credits

[JarbasAI](https://github.com/JarbasAl)

## License

[Apache-2.0](LICENSE)
