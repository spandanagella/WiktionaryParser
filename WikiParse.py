"""
Final code for wiktionary parser.
"""
from __future__ import unicode_literals
from __future__ import absolute_import
import re, requests
from utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup

PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection"
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "derived terms", "coordinate terms"
]

UNWANTED_LIST = [
    'External links',
    'Anagrams', 'References',
    'Statistics', 'See also'
]

STOPWORDS = ['to', 'a', 'the', 'as', 'an']

class WiktionaryParser(object):
    """
    Final class for Wiktionary parser.
    """

    def __init__(self):
        self.url = "https://en.wiktionary.org/wiki/"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://",
                           requests.adapters.HTTPAdapter(max_retries=2))
        self.session.mount("https://",
                           requests.adapters.HTTPAdapter(max_retries=2))
        self.language = 'english'

    def set_default_language(self, language=None):
        """
        Sets the default language of the parser object.
        """
        if language is not None:
            self.language = language.lower()
        return

    def get_default_language(self):
        """
        returns the default language of the object.
        """
        return self.language

    @staticmethod
    def get_id_list(contents, content_type):
        """
        Returns a list of IDs relating to the specific content type.
        Text can be obtained by parsing the text within span tags
        having those IDs.
        """
        if content_type == 'etymologies':
            checklist = ['etymology']
        elif content_type == 'pronunciation':
            checklist = ['pronunciation']
        elif content_type == 'translations':
            checklist = ['translations']
        elif content_type == 'definitions':
            checklist = PARTS_OF_SPEECH
        elif content_type == 'related':
            checklist = RELATIONS
        else:
            return None
        id_list = []
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = ''.join(i for i in content_tag.text
                                    if not i.isdigit()).strip().lower()
	    #print text_to_check
            if text_to_check in checklist:
		#print 'Inside checklist', text_to_check
                content_id = content_tag.parent['href'].replace('#', '')
		#print (content_index, content_id, text_to_check)
                id_list.append((content_index, content_id, text_to_check))
        return id_list

    def get_word_data(self, language):
        """
        Match language, get previous tag, get starting number.
        """
        contents = self.soup.find_all('span', {'class': 'toctext'})
        language_contents = []
        start_index = None
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if start_index is None:
            return []
        for content in contents:
            index = content.find_previous().text
            if index.startswith(start_index):
                language_contents.append(content)
        word_contents = []
        for content in language_contents:
	    #print 'Text', content.text
            if content.text not in UNWANTED_LIST:
                word_contents.append(content)
        etymology_id_list = self.get_id_list(word_contents, 'etymologies')
        definition_id_list = self.get_id_list(word_contents, 'definitions')
        relation_id_list = self.get_id_list(word_contents, 'related')
        pronunciation_id_list = self.get_id_list(word_contents, 'pronunciation')
        etymology_list = self.parse_etymologies(etymology_id_list)
        example_list = self.parse_examples(definition_id_list)
        definition_list = self.parse_definitions(definition_id_list)
        translation_id_list = self.get_id_list(word_contents, 'translations')
        translation_list = self.parse_translations(translation_id_list)
        related_words_list = self.parse_related_words(relation_id_list)
        pronunciation_list = self.parse_pronunciations(pronunciation_id_list)
	definition_index_translations = {}
	for definition_index, definition_text, definition_type in definition_list:
	    #print 'XX', definition_index, definition_type, '%s' %(definition_text)
	    translations = self.map_id_word_translations_to_definitions(definition_index, definition_type, translation_list, '%s' %(definition_text))
	    definition_index_translations[definition_index] = translations
        json_obj_list = self.make_class(
            etymology_list,
            definition_list,
            example_list,
            related_words_list,
            pronunciation_list,
	    translation_list, 
	    definition_index_translations
        )
        return json_obj_list

    def parse_pronunciations(self, pronunciation_id_list=None):
        """
        Parse pronunciations from their IDs.
        clear supertext tags first.
        separate audio links.
        """
        pronunciation_list = []
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            span_tag = self.soup.find_all('span', {'id': pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.find_next_sibling()
            for super_tag in list_tag.find_all('sup'):
                super_tag.clear()
            audio_links = []
            pronunciation_text = []
            for list_element in list_tag.find_all('li'):
                for audio_tag in list_element.find_all(
                        'div', {'class': 'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    list_element.clear()
                if list_element.text:
                    pronunciation_text.append(list_element.text)
            pronunciation_list.append(
                (pronunciation_index, pronunciation_text, audio_links))
        return pronunciation_list

    def parse_definitions(self, definition_id_list=None):
        """
        Definitions are ordered lists
        Look for the first <ol> tag
        The tag right before the <ol> tag has tenses.
        """
        definition_list = []
	#print definition_id_list
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            definition_tag = None
            while table.name != 'ol':
                definition_tag = table
                table = table.find_next_sibling()
		#print def_id, def_type, table
            definition_text = definition_tag.text + '\n'
            for element in table.find_all('li'):
                definition_text += re.sub('(\\n+)', '',
                                          element.text.strip()) + '\n'
            definition_list.append((def_index,
                                    definition_text,
                                    def_type))
        return definition_list
    
    def parse_translations(self, translation_id_list = None):
	#print translation_id_list
	"""
		Translations are given in 'NavFrame' div, unfortunately no direct mapping with pos/index.
		Keep the id (has definition) and use that to map it to index later.
	"""
	id_word_translations = {}
	index_word_translations = {}
        for trans_index, trans_id, trans_type in translation_id_list:
	    #print trans_index, trans_id, trans_type
	    for div_tag in self.soup.find_all('div', {'class': 'NavFrame'}):
		tag_id = '%s' %(div_tag.get('id'))
		if tag_id == 'None' or 'Translations' not in tag_id:
		    continue
		#print tag_id
		id_word_translations[tag_id] = {} #'index': trans_index}
		index_word_translations[trans_index] = {}
		for element in div_tag.find_all('li'):
		    for span_tag in element.find_all('span'):
			if span_tag.get('lang') is None:
			    continue
			href_element = span_tag.find('a')
			if href_element is not None:
			    language = span_tag.get('lang')
			    if not id_word_translations[tag_id].has_key(language):
			        id_word_translations[tag_id][language] = []
			    if not index_word_translations[trans_index].has_key(language):
			        index_word_translations[trans_index][language] = []
			    id_word_translations[tag_id][language].append(href_element.get('title'))
			    #if language == 'de':
			    #    print trans_index, span_tag.get('lang'), href_element.get('title')	
			    index_word_translations[trans_index][language].append(href_element.get('title'))
	    break
	#for index in index_word_translations.keys():
	#    if index_word_translations[index].has_key('de'):
	#	#print index, index_word_translations[index]['de']
	return id_word_translations
		

    def parse_examples(self, definition_id_list=None):
        """
        look for <dd> tags inside <ol> tags.
        remove data in <ul> tags.
        """
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.find_next_sibling()
            for element in table.find_all('ul'):
                element.clear()
            examples = []
            for element in table.find_all('dd'):
                example_text = element.text.strip()
                if example_text and not (example_text.startswith('(') and
                                         example_text.endswith(')')):
                    examples.append(example_text)
                element.clear()
            example_list.append((def_index, examples, def_type))
        return example_list

    def parse_etymologies(self, etymology_id_list=None):
        """
        Word etymology is either a para or a list.
        move forward till you find either.
        """
        etymology_list = []
        for etymology_index, etymology_id, _ in etymology_id_list:
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
            etymology_tag = None
            next_tag = span_tag.parent.find_next_sibling()
            while next_tag.name not in ['h3', 'h4', 'div']:
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
            if etymology_tag is None:
                etymology_text = ''
            elif etymology_tag.name == 'p':
                etymology_text = etymology_tag.text
            else:
                etymology_text = ''
                for list_tag in etymology_tag.find_all('li'):
                    etymology_text += list_tag.text + '\n'
            etymology_list.append(
                (etymology_index, etymology_text))
        return etymology_list

    def parse_related_words(self, relation_id_list=None):
        """
        Look for parent tags with <li> tags, those are related words.
        <li> tags can either be in tables or lists.
        """
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            for list_tag in parent_tag.find_all('li'):
                words.append(list_tag.text)
            related_words_list.append((related_index, words, relation_type))
        return related_words_list


    def match_definition(self, definitions, trans_definition):
	for definition in definitions:
	    definition_filtered = re.sub("[\(\[].*?[\)\]]", "", definition.lower()).replace(',', '').replace(';', '')
	    if ':' in definition_filtered:
		definition_filtered = definition_filtered.split(':')[1]
	    words = [word for word in definition_filtered.split() if word not in STOPWORDS]
	    if ('(' in definition and len(words) <=1) or len(words)==0:
		continue
	    #print words
	    if words[-1] == '.':
	        words = words[:-1]
	    if ':' in trans_definition:
		trans_definition = trans_definition.split(':')[1]
	    trans_definition = trans_definition.replace(',', '').replace(';', '')
	    trans_def_words = [word for word in trans_definition.split() if word not in STOPWORDS]
	    word_length = len(words)
	    trans_def_length = len(trans_def_words)
	    if abs(word_length - trans_def_length)>=5:
		continue
	    word_count = 0
	    for word in trans_def_words:
	        if word in words:
		    word_count +=1
	    if word_count == 0:
		continue
	    #print trans_definition, '-->', ' '.join(words), word_count, word_length, trans_def_length
	    if word_count>=trans_def_length-1 or (word_count >= word_length-2 and word_count>=trans_def_length-2): 
		#print definition.strip(), ' :: ',  trans_definition, len(words), len(trans_def_words)
		return definition.strip()
	return None
	
    def map_id_word_translations_to_definitions(self, definition_index, definition_type, id_word_translations, definition_text):
	definitions = definition_text.split('\n')
	index_translations = {}
	if definition_type == 'noun':
	    return index_translations
	for key in id_word_translations:
	    trans_definition = key.replace('Translations-', '').replace('_', ' ').replace('.2C', ',')
	    matched_def = self.match_definition(definitions, trans_definition)	   
	    if matched_def is None:
	        continue
	    for lang in id_word_translations[key].keys():
		if not index_translations.has_key(lang):
		    index_translations[lang] = []
		index_translations[lang].extend(id_word_translations[key][lang])
	    #index_translations.append(id_word_translations[key])
	return index_translations
	    

    @staticmethod
    def make_class(etymology_list,
                   definition_list,
                   example_list,
                   related_words_list,
                   pronunciation_list,
		   translation_dict, 
		   definition_index_translations
                  ):
        """
        Takes all the data and makes classes.
        """
	#print translation_dict.keys()
        json_obj_list = []
        if not etymology_list:
            etymology_list = [('', '')]
        for etymology_index, etymology_text in etymology_list:
            data_obj = WordData()
            data_obj.etymology = etymology_text
            for pronunciation_index, pronunciations, audio_links in pronunciation_list:
                if pronunciation_index.startswith(etymology_index) \
                or pronunciation_index.count('.') == etymology_index.count('.'):
                    data_obj.pronunciations = pronunciations
                    data_obj.audio_links = audio_links
            for definition_index, definition_text, definition_type in definition_list:
		#print definition_index, type(definition_text)
		#index_translations = map_id_word_translations_to_definitions(definition_index, translation_dict, definition_text)
		#print definition_index, len(definition_index_translations[definition_index])
		if definition_index_translations.has_key(definition_index):
		    translations = definition_index_translations[definition_index]
		    data_obj.translations.append(translations)
                if definition_index.startswith(etymology_index) \
                or definition_index.count('.') == etymology_index.count('.'):
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in example_list:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in related_words_list:
                        if related_word_index.startswith(definition_index) \
                        or (related_word_index.startswith(etymology_index) \
                        and related_word_index.count('.') == definition_index.count('.')):
                            words = None
                            try:
                                words = next(
                                    item.words for item in def_obj.related_words
                                    if item.relationship_type == relation_type)
                            except StopIteration:
                                pass  
                            if words is not None:
                                words += related_words
                                break
                            related_word_obj = RelatedWord()
                            related_word_obj.words = related_words
                            related_word_obj.relationship_type = relation_type
                            def_obj.related_words.append(related_word_obj)
                    data_obj.definition_list.append(def_obj)
            json_obj_list.append(data_obj.to_json())
        return json_obj_list

    def fetch(self, word, language=None):
        """
        main function.
        subject to change.
        """
        language = self.language if not language else language
        response = self.session.get(self.url + word + '?printable=yes')
        self.soup = BeautifulSoup(response.text, 'html.parser')
        #self.get_word_translations()
        return self.get_word_data(language.lower())
