# -*- coding: utf-8 -*-
import urllib,simplejson

def translate(word, from_l, to_l):
    word = urllib.quote(word)
    url = 'http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%s&langpair=%s%%7C%s'%(word, from_l, to_l)
    src =  urllib.urlopen(url).read()
    convert = simplejson.loads(src)
    results = convert['responseData']['translatedText']
    return results
def detect_lang(word):
    word = urllib.quote(word)
    url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=%s'%word
#    http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=Ciao%20mondo
    src =  urllib.urlopen(url).read()
    convert = simplejson.loads(src)
    results = convert['responseData']['language']
    return results

word = 'Как жизнь, унылые люди?'
from_l = 'en'
to_l = 'ja'

print translate(word,from_l,to_l)
print translate(word, detect_lang(word), 'ja')
#http://code.google.com/apis/ajaxlanguage/documentation/reference.html#_fonje_detect
