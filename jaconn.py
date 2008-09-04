# -*- coding: utf-8 -*-
import xmpp, inspect, re
import ConfigParser

class bot:
    comm_pref = 'nia_'
    admin_comm_pref = 'admin_'
    def __init__(self):
        user, confs, ignore = self.config(False)
        self.JID = user['jid']
        self.PASSWD = user['passwd']
        self.NICK= user['nick']
        self.admin = xmpp.protocol.JID(user['admin'])
        self.CONFS = confs
        self.commands = {}
        self.admin_commands = {}
        self.ignore = ignore

        self.resource= 'Nia Teppelin'
        self.version = '0.666'
        self.os = '.NET Windows Vista'
        self.help = {'com':[],'admin':[]}
        for (name, value) in inspect.getmembers(self):
#            print name, value
            if inspect.ismethod(value) and name.startswith(self.comm_pref):
                self.commands[name[len(self.comm_pref):]] = value
                self.help['com'].append(name[len(self.comm_pref):])
            if inspect.ismethod(value) and name.startswith(self.admin_comm_pref):
                self.admin_commands[name[len(self.admin_comm_pref):]] = value
                self.help['admin'].append(name[len(self.admin_comm_pref):])
        #print self.commands, self.admin_commands
        self.help = {'com':', '.join(self.help['com']),'admin':', '.join(self.help['admin'])}


    def config(self,flag,confs=None,ignore=None):
        config = ConfigParser.ConfigParser()
        def config_write():
            config.add_section('general')
            config.set('general', 'jid', self.JID)
            config.set('general', 'passwd', self.PASSWD)
            config.set('general', 'nick', self.NICK)
            config.set('general', 'admin', self.admin)
            config.set('general', 'ignore', ','.join(ignore))
            config.set('general', 'confs', ','.join(confs) )
            config.write(open('nia.cfg','w'))
        def config_read():
            config.read('nia.cfg')
            user = {'jid':config.get('general','jid'),
                'passwd':config.get('general','passwd'),
                'nick':config.get('general','nick'),
                'admin':config.get('general','admin')}
            confs = config.get('general','confs').decode('utf-8').split(',')
            ignore = config.get('general','ignore').decode('utf-8').split(',')
            return user, confs, ignore
        if flag:
            config_write()
        else:
            return config_read()


    def connect(self):
        '''Подключение к серверу'''
        self.jid = xmpp.protocol.JID(self.JID)
        self.conn=xmpp.Client(self.jid.getDomain(),debug=[])
        self.conn.connect()
        self.conn.auth(self.jid.getNode(),self.PASSWD,'nyaa~')
        self.conn.sendInitPresence()
        self.conn.RegisterHandler('message',self.get_mes)
        self.conn.RegisterHandler('iq', self.version, typ='get',\
                                 ns=xmpp.NS_VERSION)

    def version(self, conn, iq):
        """Returns reply to iq:version"""
        iq=iq.buildReply('result')
        qp=iq.getTag('query')
        qp.setTagData('name', self.resource)
        qp.setTagData('version', self.version)
        qp.setTagData('os', self.os)
        conn.send(iq)
        raise xmpp.NodeProcessed
 
    def join_room(self, confs):
        for conf in confs:
            self.p=xmpp.Presence(to='%s/%s'%(conf,self.NICK))
            self.p.setTag('Nia',namespace=xmpp.NS_MUC).setTagData('password','')
            self.p.getTag('Nia').addChild('history',{'maxchars':'0','maxstanzas':'0'})
            self.conn.send(self.p)
    def leave_room(self, confs):
        for conf in confs:
            to = '%s/%s'%(conf,self.NICK)
            self.send_system(to,'offline','unavailable')
    def reconnect(self):
        self.connect()
        self.join_room(self.CONFS)
    def online(self):
        self.connect()
        self.join_room(self.CONFS)
        while True:
            try:
                self.conn.Process(1)
            except xmpp.protocol.XMLNotWellFormed:
                self.reconnect()


    def send_chat(self,type,to,text):
        ''' Отправка в чат обычного сообщения.
        type - тип сообщения, groupchat или chat
        to - кому отправляем
        text - отправляемый текст'''
        self.conn.send(xmpp.protocol.Message(to,text,type))

    def send_system(self,to,msg,type):
        '''Отправка системного сообщения. Статусы'''
        print to, msg, type
        self.conn.send(xmpp.protocol.Presence(to=to,status=msg,typ=type))
    def XMLescape(self, text):
        return xmpp.simplexml.XMLescape(text)

    def send_xml(self,type,to,text,extra):
        '''Отправка сообщения в форме xhtml'''
        xhtml = '''
        <html xmlns='http://jabber.org/protocol/xhtml-im'>
        <body xml:lang='en-US' xmlns='http://www.w3.org/1999/xhtml'>
        %s
        </body></html>
        '''%extra
        
        self.conn.send("<message to='%s' type='%s'><body>%s</body>%s</message>"%(to,type,text,xhtml))

    def get_mes(self,conn,mess):
        ''' Получение сообщений и обработка'''
        self.type=mess.getType()
        self.nick=mess.getFrom()
        self.text=mess.getBody()
        #print self.type.encode('utf-8'), self.nick.encode('utf-8'), self.text.encode('utf-8')
        if self.ignore.count(self.nick.getResource()):
            pass
        elif self.type == 'groupchat':
            if re.match('^%s[\W]'%self.NICK, self.text):
                self.to = '%s@%s'%(self.nick.getNode(),self.nick.getDomain())
                nick = self.nick.getResource()
                text = re.findall('^%s[\W]{0,2}[\s]{1,3}(.*?)$'%self.NICK,self.text)[0]

                tmp = text.split(' ',1)
                if len(tmp) >= 2:
                    cmd = tmp[0]
                    args = tmp[1]
                elif len(tmp) == 1:
                    cmd = tmp[0]
                    args = ''

                if self.commands.has_key(cmd):
                    '''
                    True - chat
                    False - xml
                    '''
                    result = self.commands[cmd](args)
                    '''
                    if result[0]:
                        text = result[1]
                        self.send_chat(self.type,to,text)
                    else:
                        text,extra = result[1],result[2]
                        self.send_xml(self.type, to, text, extra)
                    '''
                elif self.admin_commands.has_key(cmd):
                    if nick == self.admin.getNode():
                        result = self.admin_commands[cmd](self.nick,args)
                        if result:
                            text = result
                            self.send_chat(self.type,self.to,text)
                        else: pass
                    else: self.send_chat(self.type, self.to, '%s~ nyaaa? Access denied...'%nick)
                else:  self.send_chat(self.type, self.to, '%s~ nyaaa? Type "help"...'%nick)
            else: return

        elif self.type == 'chat':
            if '%s@%s'%(self.nick.getNode(),self.nick.getDomain()) == self.admin:
                tmp = self.text.split(' ',1)
                print tmp
                if len(tmp) >= 2:
                    cmd = tmp[0]
                    args = tmp[1]
                elif len(tmp) == 1:
                    cmd = tmp[0]
                    args = ''
                print cmd, args
                if self.admin_commands.has_key(cmd):
                    self.admin_commands[cmd](args)


    def send_iq(self,_type, to):
        self.conn.send(xmpp.protocol.Iq(to=to,typ=_type ,queryNS=xmpp.NS_VERSION))
    def get_iq(self,conn,mess):
        print mess
        self.query = mess 
        ''' 
        query = mess.getTag('query')
        client = '%s %s'%(query.getTagData('name'),query.getTagData('version') )
        os = query.getTagData('os')
        self._version=(client, os)
        print self._version
        '''






'''
http://code.google.com/p/robocat/source/browse/trunk/start.py


<iq from='apkawa@jabber.ru/LoR' to='apkawa@jabber.ru/LoR' xml:lang='ru' id='1856' type='result'>
<query xmlns='jabber:iq:version'>
<name>Gajim</name>
<version>0.11.4.4-svn</version>
<os>Arch Linux</os>
</query>
</iq>


http://www.linux.org.ru/view-message.jsp?msgid=2591531#2591657

<presence to="жабы@conference.jabber.ru/Apkawa" xml:lang="ru" type="unavailable" id="1345">
<status>offline</status>
</presence>

<presence from='жабы@conference.jabber.ru/Apkawa' to='apkawa@jabber.ru/LoR' xml:lang='ru' type='unavailable' id='1345'>
<status>offline</status>
<x xmlns='http://jabber.org/protocol/muc#user'>
<item affiliation='owner' role='none'/>
</x>
</presence>
'''

