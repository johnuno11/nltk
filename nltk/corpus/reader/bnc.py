# Natural Language Toolkit: Plaintext Corpus Reader
#
# Copyright (C) 2008 University of Pennsylvania
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
# URL: <http://nltk.sf.net>
# For license information, see LICENSE.TXT

"""
Corpus reader for the XML version of the British National Corpus.
"""
__docformat__ = 'epytext en'

from nltk.corpus.reader.xmldocs import XMLCorpusReader
import nltk.etree.ElementTree as ET
from nltk.corpus.reader.api import *
from nltk.corpus.reader.util import *
from nltk.corpus.reader.xmldocs import *
import re

class BNCCorpusReader(XMLCorpusReader):
    """
    Corpus reader for the XML version of the British National Corpus.
    For access to the complete XML data structure, use the L{xml()}
    method.  For access to simple word lists and tagged word lists, use
    L{words()}, L{sents()}, L{tagged_words()}, and L{tagged_sents()}.
    """
    def __init__(self, root, files, lazy=True):
        XMLCorpusReader.__init__(self, root, files)
        self._lazy = lazy
    
    def words(self, files=None, strip_space=True, stem=False):
        """
        @return: the given file or files as a list of words
            and punctuation symbols.
        @rtype: C{list} of C{str}
        
        @param strip_space: If true, then strip trailing spaces from
            word tokens.  Otherwise, leave the spaces on the tokens.
        @param stem: If true, then use word stems instead of word strings.
        """
        if self._lazy:
            return concat([BNCWordView(filename, False, None,
                                       strip_space, stem)
                           for filename in self.abspaths(files)])
        else:
            return concat([self._words(filename, False, None,
                                       strip_space, stem)
                           for filename in self.abspaths(files)])

    def tagged_words(self, files=None, c5=False, strip_space=True, stem=False):
        """
        @return: the given file or files as a list of tagged
            words and punctuation symbols, encoded as tuples
            C{(word,tag)}.
        @rtype: C{list} of C{(str,str)}
        
        @param c5: If true, then the tags used will be the more detailed
            c5 tags.  Otherwise, the simplified tags will be used.
        @param strip_space: If true, then strip trailing spaces from
            word tokens.  Otherwise, leave the spaces on the tokens.
        @param stem: If true, then use word stems instead of word strings.
        """
        if c5: tag = 'c5'
        else: tag = 'pos'
        if self._lazy:
            return concat([BNCWordView(filename, False, tag, strip_space, stem)
                           for filename in self.abspaths(files)])
        else:
            return concat([self._words(filename, False, tag, strip_space, stem)
                           for filename in self.abspaths(files)])

    def sents(self, files=None, strip_space=True, stem=False):
        """
        @return: the given file or files as a list of
            sentences or utterances, each encoded as a list of word
            strings.
        @rtype: C{list} of (C{list} of C{str})
        
        @param strip_space: If true, then strip trailing spaces from
            word tokens.  Otherwise, leave the spaces on the tokens.
        @param stem: If true, then use word stems instead of word strings.
        """
        if self._lazy:
            return concat([BNCWordView(filename, True, None, strip_space, stem)
                           for filename in self.abspaths(files)])
        else:
            return concat([self._words(filename, True, None, strip_space, stem)
                           for filename in self.abspaths(files)])

    def tagged_sents(self, files=None, c5=False, strip_space=True,
                     stem=False):
        """
        @return: the given file or files as a list of
            sentences, each encoded as a list of C{(word,tag)} tuples.
        @rtype: C{list} of (C{list} of C{(str,str)})
            
        @param c5: If true, then the tags used will be the more detailed
            c5 tags.  Otherwise, the simplified tags will be used.
        @param strip_space: If true, then strip trailing spaces from
            word tokens.  Otherwise, leave the spaces on the tokens.
        @param stem: If true, then use word stems instead of word strings.
        """
        if c5: tag = 'c5'
        else: tag = 'pos'
        if self._lazy:
            return concat([BNCWordView(filename, True, tag, strip_space, stem)
                           for filename in self.abspaths(files)])
        else:
            return concat([self._words(filename, True, tag, strip_space, stem)
                           for filename in self.abspaths(files)])

    def _words(self, filename, bracket_sent, tag, strip_space, stem):
        """
        Helper used to implement the view methods -- returns a list of
        words or a list of sentences, optionally tagged.
        
        @param filename: The name of the underlying file.
        @param bracket_sent: If true, include sentence bracketing.
        @param tag: The name of the tagset to use, or None for no tags.
        @param strip_space: If true, strip spaces from word tokens.
        @param stem: If true, then substitute stems for words.
        """
        result = []
        
        xmldoc = ElementTree.parse(filename).getroot()
        for xmlsent in xmldoc.findall('.//s'):
            sent = []
            for xmlword in _all_xmlwords_in(xmlsent):
                word = xmlword.text
                if strip_space or stem: word = word.strip()
                if stem: word = xmlword.get('hw', word)
                if tag == 'c5':
                    word = (word, xmlword.get('c5'))
                elif tag == 'pos':
                    word = (word, xmlword.get('pos', xmlword.get('c5')))
                sent.append(word)
            if bracket_sent:
                result.append(BNCSentence(xmlsent.attrib['n'], sent))
            else:
                result.extend(sent)

        assert None not in result
        return result

def _all_xmlwords_in(elt, result=None):
    if result is None: result = []
    for child in elt:
        if child.tag in ('c', 'w'): result.append(child)
        else: _all_xmlwords_in(child, result)
    return result

class BNCSentence(list):
    """
    A list of words, augmented by an attribute C{num} used to record
    the sentence identifier (the C{n} attribute from the XML).
    """
    def __init__(self, num, items):
        self.num = num
        list.__init__(self, items)

class BNCWordView(XMLCorpusView):
    """
    A stream backed corpus view specialized for use with the BNC corpus.
    """
    def __init__(self, filename, sent, tag, strip_space, stem):
        """
        @param filename: The name of the underlying file.
        @param sent: If true, include sentence bracketing.
        @param tag: The name of the tagset to use, or None for no tags.
        @param strip_space: If true, strip spaces from word tokens.
        @param stem: If true, then substitute stems for words.
        """
        if sent: tagspec = '.*/s'
        else: tagspec = '.*/s/(.*/)?(c|w)'
        self._sent = sent
        self._tag = tag
        self._strip_space = strip_space
        self._stem = stem

        XMLCorpusView.__init__(self, filename, tagspec)
        
        # Read in a tasty header.
        stream = codecs.open(filename, 'rb', self._encoding)
        self.read_block(stream, '.*/teiHeader$', self.handle_header)

        # Reset tag context.
        self._tag_context = {0: ()}


    title = None #: Title of the document.
    author = None #: Author of the document.
    editor = None #: Editor
    resps = None #: Statement of responsibility

    def handle_header(self, elt, context):
        # Set up some metadata!
        titles = elt.findall('titleStmt/title')
        if titles: self.title = '\n'.join(
            [title.text.strip() for title in titles])

        authors = elt.findall('titleStmt/author')
        if authors: self.author = '\n'.join(
            [author.text.strip() for author in authors])

        editors = elt.findall('titleStmt/editor')
        if editors: self.editor = '\n'.join(
            [editor.text.strip() for editor in editors])

        resps = elt.findall('titleStmt/respStmt')
        if resps: self.resps = '\n\n'.join([
            '\n'.join([resp_elt.text.strip() for resp_elt in resp])
            for resp in resps])

    def handle_elt(self, elt, context):
        if self._sent: return self.handle_sent(elt)
        else: return self.handle_word(elt)
        
    def handle_word(self, elt):
        word = elt.text
        if self._strip_space or self._stem:
            word = word.strip()
        if self._stem:
            word = elt.get('hw', word)
        if self._tag == 'c5':
            word = (word, elt.get('c5'))
        elif self._tag == 'pos':
            word = (word, elt.get('pos', elt.get('c5')))
        return word

    def handle_sent(self, elt):
        sent = []
        for child in elt:
            if child.tag == 'mw':
                sent += [self.handle_word(w) for w in child]
            elif child.tag in ('w','c'):
                sent.append(self.handle_word(child))
            else:
                raise ValueError('Unexpected element %s' % child.tag)
        return BNCSentence(elt.attrib['n'], sent)

