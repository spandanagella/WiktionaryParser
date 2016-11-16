from WikiParse import WiktionaryParser
import sys
parser = WiktionaryParser
parser = WiktionaryParser()
#print word

query_word = sys.argv[1]
word = parser.fetch(query_word)
languages = sys.argv[2].split(',')
language_words = {lang:[] for lang in languages}
for x in word:
    for trans in x['translations']:
	for lang in languages:
	    if trans.has_key(lang):
		new_words = [word.split('(')[0] for word in trans[lang] if word not in language_words[lang]]
		language_words[lang].extend(new_words)
for lang in languages:
    print lang, set(language_words[lang])

