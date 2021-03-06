#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Nia - бот написаный на Python.
Разработчик - apkawa@gmail.com

Лицензия - GPLv3
'''
from jaconn import bot

import re
from random import randint
import urllib
from simplejson import loads
from xml.sax.saxutils import unescape


class Nia(bot):
    def LOG(self, conf, nick, body):
        if self.logging:
            from nia_sql import sql
            s = sql()
            body = re.sub('\'','',body)
            self.DEBUG(body)
            s.write(conf, nick, body)

    def nia_help(self,args):
        '''Lists of possible functions'''
        if args:
            if self.commands.has_key(args):
                halp = self.commands[args].__doc__
            elif self.admin_commands.has_key(args):
                halp = self.admin_commands[args].__doc__
            else:
                halp = 'Nyaaa? This command does not...'
        else:
            halp ='''List of functions
            User command: %s
            Master command: %s

            Type help <command> to learn more
            '''%(self.help['com'],self.help['admin'])
        self.send(halp)

    def nia_tr(self,args):
        '''Usage: tr <from lang> <to lang> <text>
        Example: tr en ja Hello world!
        Translated text into another language.
        en - English
        ru - Russian
        ja - Japan
        ko - Korean
        de - German
        fr - French
        it - Italian
        es - Spanish
        et - Estonian
        hi - Hindi
        '''

        tmp = re.findall('([\w]{2})[\s]*?([\w]{2})[\s]*?(.*?)$',args)
        if tmp:
            tmp = tmp[0]
            from_l, to_l, word = tmp[0],tmp[1],tmp[2]
            self.send( translated(word, to_l, from_l))
        else: self.send( 'Nyaa? Bad request...')
    def nia_say(self,args):
        '''Usage: say <text> 
        Send a message on behalf Bot'''
        self.send( args)
    def nia_show(self,args):
        '''Usage: show http://example.com/image.jpg
        Show a picture to chat. Works only in Gajim.'''
        if re.search('http://',args):
            text = self.XMLescape(args)
            extra = '<a href="%s"><img src="%s"/></a>'%(text,text)
            self.send(False, text, extra)
        else:
            self.send( 'Nyaaa? This does not link...')

    def nia_google(self, args):
        '''Search in google.com'''
        flag, text, extra = google(args,'web')
        self.send(text, extra, flag)
    def nia_enwiki(self, args):
        '''Search in en.wikipedia.org'''
        flag, text, extra = google('site:http://en.wikipedia.org %s'%args,'web')
    def nia_ruwiki(self, args):
        '''Search in http://ru.wikipedia.org'''
        flag, text, extra = google('site:http://ru.wikipedia.org %s'%args,'web')
        self.send(text, extra, flag)
    def nia_wa(self, args):
        '''Search in world-art.ru'''
        flag, text, extra = google('site:http://www.world-art.ru %s'%args,'web')
        self.send(text, extra, flag)
    def nia_adb(self, args):
        '''Search in anidb.info'''
        flag, text, extra = google('site:http://anidb.info %s'%args,'web')
        self.send(text, extra, flag)
    def nia_lurk(self, args):
        '''Search in lurkmore.ru'''
        flag, text, extra = google('site:http://lurkmore.ru/ %s'%args,'web')
        self.send(text, extra, flag)
    def nia_gpic(self, args):
        '''Usage: gpic <word>
        Find a picture in google.com and show to chat. Works only in Gajim.'''
        flag, text, extra = google(args,'images')
        self.send(text, extra, flag)

    def nia_alias(self, args):
        '''Usage: alias <cmd> = '<command, arguments>'
        Set alias'''
        tmp = re.findall('^(.*?)(?:[\s]{0,})=(?:[\s]{0,})\'(.*)\'',args)
        if tmp:
            tmp = tmp[0]
            if not self.commands.has_key(tmp[0]) and not self.alias.has_key(tmp[0]) and not self.alias.has_key(tmp[0]):
                self.alias[tmp[0]] = tmp[1]
                mess = 'Set alias %s = %s'%(tmp[0],tmp[1])
            else:
                mess = 'Nyaaa... Name alias should not overlap with existing commands and alias.'
        else:
            mess = 'Nyaaa... Invalid syntax. Type "help alias".'
        self.send(mess)

    def nia_rmalias(self,args):
        '''Usage: rmalias <alias>
        Remove alias'''
        if self.alias.has_key(args):
            del self.alias[args]
    def nia_lsalias(self,args):
        '''Usage: lsalias
        List all alias'''
        self.send('List alias:\n%s'%'\n'.join(['%s = %s'%(i,self.alias[i]) for i in self.alias]))

        

    def nia_version(self,args):
        '''Usage: version [|<Nick>]'''
        nick = self.nick
        conf = '%s@%s'%(nick.getNode(),nick.getDomain())
        self.toversion = ''
        args = re.findall('^(.*?)(?:|[\s])$',args)[0]
        if not args:
            to = nick
        else:
            to = '%s/%s'%(conf,args)
        self.send_iq('get',to)
    
    def admin_join(self,nick,conf):
        '''Usage: join example@conference.example.com
        Go to room bot'''
        if not conf in self.CONFS:
            self.CONFS.append(conf)
            self.join_room((conf,))
        else: pass

    def admin_leave(self,nick,conf):
        '''Usage: leave example@conference.example.com
        Exit the room. Without arguments - to emerge from the current room.'''
        if not conf:
            conf = '%s@%s'%(nick.getNode(),nick.getDomain())
        to = '%s/%s'%(conf,self.NICK)
        self.send_system(to,'offline','unavailable')
        if self.CONFS.count(conf):
            self.CONFS.remove(conf)

    def admin_joined(self,nick,conf):
        '''Usage: joined
        Show the list of rooms in which the bot.'''
        self.send(' '.join(self.CONFS))

    def admin_ignore(self,nick,user):
        '''Usage: ignore <user>
        Ignore bot user.'''
        user = '%s/%s'%(self.to,user)
        if self.type_f or (user in self.ignore):
            self.ignore.append(user)
        return False

    def admin_noignore(self,nick,user):
        '''Usage: noignore <user>
        Remove from user ignore'''
        for i in xrange(self.ignore.count(user)):
            self.ignore.remove(user)

    def admin_lsignore(self,nick,user):
        '''Usage: lsignore
        Show list ignored users'''
        self.send(' '.join(self.ignore))

    def admin_savecfg(self,nick,args):
        '''Usage: savecfg
        Save current configuration'''
        self.config(True,self.CONFS,self.ignore)

    def _admin_restart(self,nick,args):
        '''Перезапустить бота.'''
        print 'restarting'
        self.leave_room(self.CONFS)
        os.spawnl(os.P_NOWAIT, 'python', 'python' ,'nia.py')

    def admin_exit(self,nick,args):
        '''Usage: exit
        Poweroff bot.'''
        sys.exit()



def google(word,type):
    def web(results):
        if results:
            url = urllib.unquote(results[0]['url'])
            title1 = results[0]['titleNoFormatting']
            title2 = results[0]['title']
            content = re.sub('(<b>)|(</b>)','',results[0]['content'])
            text = '%s\n%s\n%s'%(title1,content,url)
            text = re.sub('&#39;','\'',unescape(text))
            #print text

            extra = '''<a href="%s">%s</a>
            <p>%s</p>
            '''%(url,title2,content)
            return True, text, extra
        else: return True, 'Nyaaa... Ничего не нашла.', ''
    def images(results):
        if results:
            imgurl = results[randint(0,len(results)-1)]['unescapedUrl']
            extra = '<a href="%s"><img src="%s"/></a>'%(imgurl,imgurl)
            return False,imgurl, extra
        else: return True, 'Nyaaa... Ничего не нашла.', ''
    #http://code.google.com/apis/ajaxsearch/documentation/reference.html#_intro_fonje
    word = urllib.quote(word.encode('utf-8'))
    src =  urllib.urlopen('http://ajax.googleapis.com/ajax/services/search/%s?v=1.0&q=%s&hl=ru'%(type,word)).read()
    convert = loads(src)
    results = convert['responseData']['results']
    if type == 'web':
        return web(results)
    if type == 'images':
        return images(results)


def translated(word,  to_l, from_l=None):
    '''Usage: tr <from lang> <to lang> <text>
    Example: tr en ja Hello world!
    Translated text into another language.
    en - English
    ru - Russian
    uk - Ukrainian
    ja - Japan
    zn - Chinese
    ko - Korean
    de - German
    fr - French
    it - Italian
    es - Spanish
    et - Estonian
    hi - Hindi
    sa - Sanskrit
    '''
    google_lang = {\
          'AFRIKAANS' : 'af',       'ALBANIAN' : 'sq',  'AMHARIC' : 'am',
          'ARABIC' : 'ar',          'ARMENIAN' : 'hy',  'AZERBAIJANI' : 'az',
          'BASQUE' : 'eu',          'BELARUSIAN' : 'be',  'BENGALI' : 'bn',  
          'BIHARI' : 'bh',          'BULGARIAN' : 'bg',  'BURMESE' : 'my',
          'CATALAN' : 'ca',         'CHEROKEE' : 'chr',
          'CHINESE' : 'zh',          'CHINESE_SIMPLIFIED' : 'zh-CN',          'CHINESE_TRADITIONAL' : 'zh-TW',
          'CROATIAN' : 'hr',         'CZECH' : 'cs',      'DANISH' : 'da',
          'DHIVEHI' : 'dv',          'DUTCH': 'nl',       'ENGLISH' : 'en',
          'ESPERANTO' : 'eo',        'ESTONIAN' : 'et',   'FILIPINO' : 'tl',
          'FINNISH' : 'fi',          'FRENCH' : 'fr',     'GALICIAN' : 'gl',
          'GEORGIAN' : 'ka',         'GERMAN' : 'de',     'GREEK' : 'el',
          'GUARANI' : 'gn',          'GUJARATI' : 'gu',   'HEBREW' : 'iw',
          'HINDI' : 'hi',            'HUNGARIAN' : 'hu',  'ICELANDIC' : 'is',
          'INDONESIAN' : 'id',       'INUKTITUT' : 'iu',  'ITALIAN' : 'it',
          'JAPANESE' : 'ja',         'KANNADA' : 'kn',    'KAZAKH' : 'kk',
          'KHMER' : 'km',            'KOREAN' : 'ko',     'KURDISH': 'ku',
          'KYRGYZ': 'ky',            'LAOTHIAN': 'lo',    'LATVIAN' : 'lv',
          'LITHUANIAN' : 'lt',       'MACEDONIAN' : 'mk',  'MALAY' : 'ms',
          'MALAYALAM' : 'ml',        'MALTESE' : 'mt',    'MARATHI' : 'mr',
          'MONGOLIAN' : 'mn',        'NEPALI' : 'ne',     'NORWEGIAN' : 'no',
          'ORIYA' : 'or',            'PASHTO' : 'ps',     'PERSIAN' : 'fa',
          'POLISH' : 'pl',           'PORTUGUESE' : 'pt-PT',          'PUNJABI' : 'pa',
          'ROMANIAN' : 'ro',         'RUSSIAN' : 'ru',    'SANSKRIT' : 'sa',
          'SERBIAN' : 'sr',          'SINDHI' : 'sd',     'SINHALESE' : 'si',
          'SLOVAK' : 'sk',           'SLOVENIAN' : 'sl',  'SPANISH' : 'es',
          'SWAHILI' : 'sw',          'SWEDISH' : 'sv',    'TAJIK' : 'tg',
          'TAMIL' : 'ta',            'TAGALOG' : 'tl',    'TELUGU' : 'te',
          'THAI' : 'th',             'TIBETAN' : 'bo',    'TURKISH' : 'tr',
          'UKRAINIAN' : 'uk',        'URDU' : 'ur',       'UZBEK' : 'uz',
          'UIGHUR' : 'ug',           'VIETNAMESE' : 'vi'  
        }
    def transl(o_word, from_l, to_l):
        word = urllib.quote(o_word.encode('utf-8'))
        url = 'http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%s&langpair=%s%%7C%s'%(word, from_l, to_l)
        src =  urllib.urlopen(url).read()
        convert = loads(src)
        status = convert['responseStatus']
        #print status, type(status), convert
        if status == 200:
            results = convert['responseData']['translatedText']
            return results
        else: return o_word
    def detect_lang(word):
        word = urllib.quote(word.encode('utf-8'))
        url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=%s'%word
        src =  urllib.urlopen(url).read()
        convert = loads(src)
        results = convert['responseData']['language']
        #print results
        return results

    transl =  transl(word, from_l, to_l)
    return transl
#http://code.google.com/apis/ajaxlanguage/documentation/reference.html#_fonje_detect


if __name__ == '__main__':
    nia = Nia()
    nia.online()

'''
некоторые идеи были взяты из:
    http://paste.org.ru/?ffxty8
    http://paste.org.ru/?9iuvw2
    http://wiki.wjsullivan.net/collaboration.cgi/SnakeBot

'''
