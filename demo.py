from WikiParse import WiktionaryParser
import sys
parser = WiktionaryParser
parser = WiktionaryParser()
#print word
query_word = sys.argv[1]
word = parser.fetch(query_word)
languages = sys.argv[2].split(',')
for x in word:
    for trans in x['translations']:
	for lang in languages:
	    if trans.has_key(lang):
		print lang, trans[lang]
