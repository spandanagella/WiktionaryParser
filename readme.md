###Wiktionary Parser

A python project which parses word content from Wiktionary in an easy to use JSON format.
Right now, it parses etymologies, definitions, pronunciations, examples, audio links and related words.

Modified the repo from https://github.com/Suyash458/WiktionaryParser

Current version hanfles, extracting translations for the word in other languages. To make things simpler, currently only extracting verb translations.


####JSON structure

```json
[{
    "pronunciations": ["list of pronunciations"],
    "definitions": [{
        "relatedWords": [{
            "relationshipType": "word relationship type",
            "words": ["list of related words"]
        }],
        "text": "definition text",
        "partOfSpeech": "part of speech",
        "exampleUses": ["list of examples"]
    }],
    "etymology": "etymology text",
    "audioLinks": ["list of audio pronunciation links"]
    "translations": {dict of translations as per language}
}]
```

####Installation

#####Using pip 
* run `pip install wiktionaryparser`

#####From Source
* Clone the repo or download the zip
* Make sure you have pip installed
* `cd` to the folder
* run `pip install -r "requirements.txt"`

####Usage

 - Import the WiktionaryParser class.
 - Initialize an object and use the fetch("word", "language") method.
 - The default language is English.
 - The default language can be changed using the set_default_language method.

####Examples

```python
>>> from wiktionaryparser import WiktionaryParser
>>> parser = WiktionaryParser()
>>> word = parser.fetch('test')
>>> another_word = parser.fetch('test','french')
>>> parser.set_default_language('french')

```

####DEMO
python demo.py ride de,fr,es,nl,it

Output:
de [u'reiten', u'fahren', u'fahren']
fr [u'rouler', u'monter', u'chevaucher', u'monter', u'monter', u'conduire']
es [u'montar', u'cabalgar', u'pasear', u'conducir']
nl [u'rijden', u'rijden']
it [u'cavalcare', u'guidare', u'andare in bici (page does not exist)', u'guidare', u'andare in macchina (page does not exist)']


####Requirements

 - requests==2.7.0
 - beautifulsoup4==4.4.0

####Contributions

