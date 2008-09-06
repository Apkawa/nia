# -*- coding: utf-8 -*-
import xmpp, inspect, re
import ConfigParser

class bot:
    def DEBUG(self, text=None):
        '''Режим отладки и тестирования'''
        if self.debug:
            self.config_file = 'nia_test.cfg'
            print unicode(text)

    comm_pref = 'nia_'
    admin_comm_pref = 'admin_'
    def __init__(self):
        self.debug = 0 

        self.config_file = 'nia.cfg'
        self.resource= 'Nia Teppelin .NET'
        self.version = '0.666'
        self.os = 'Windows Vista'

        self.DEBUG()

        user, confs, ignore, alias = self.config(False)
        self.JID = user['jid']
        self.PASSWD = user['passwd']
        self.NICK= unicode(user['nick'],'utf-8')
        self.admin = xmpp.protocol.JID(user['admin'])
        self.CONFS = confs
        self.ignore = ignore
        self.alias = alias 

        self.commands = {}
        self.admin_commands = {}
        self.help = {'com':[],'admin':[]}
        for (name, value) in inspect.getmembers(self):
            if inspect.ismethod(value) and name.startswith(self.comm_pref):
                self.commands[name[len(self.comm_pref):]] = value
                self.help['com'].append(name[len(self.comm_pref):])
            if inspect.ismethod(value) and name.startswith(self.admin_comm_pref):
                self.admin_commands[name[len(self.admin_comm_pref):]] = value
                self.help['admin'].append(name[len(self.admin_comm_pref):])
        self.help = {'com':', '.join(self.help['com']),'admin':', '.join(self.help['admin'])}



    def config(self,flag,confs=None,ignore=None):
        config = ConfigParser.ConfigParser()
        def config_write():
            config.add_section('alias')
            for key in self.alias:
                config.set('alias', key, self.alias[key])
            config.add_section('general')
            config.set('general', 'jid', self.JID)
            config.set('general', 'passwd', self.PASSWD)
            config.set('general', 'nick', self.NICK)
            config.set('general', 'admin', self.admin)
            config.set('general', 'ignore', ','.join(ignore))
            config.set('general', 'confs', ','.join(confs) )
            config.write(open(self.config_file,'w'))
        def config_read():
            alias = {}
            config.read(self.config_file)
            user = {'jid':config.get('general','jid'),
                'passwd':config.get('general','passwd'),
                'nick':config.get('general','nick'),
                'admin':config.get('general','admin')}
            confs = config.get('general','confs').decode('utf-8').split(',')
            ignore = config.get('general','ignore').decode('utf-8').split(',')
            for key in config.options('alias'):
                alias[key] = config.get('alias',key)
            return user, confs, ignore, alias
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
        self.conn.RegisterDisconnectHandler(self.conn.reconnectAndReauth)
        self.conn.RegisterHandler('message',self.get_mes)
        self.conn.RegisterHandler('iq', self.iq_version, typ='get', ns=xmpp.NS_VERSION)
        self.conn.RegisterHandler('iq', self.get_iq, typ='result', ns=xmpp.NS_VERSION)

    def iq_version(self, conn, iq):
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


    def send(self, text, extra=None, flag=True):
        '''
        True - chat
        False - xml
        '''
        if flag:
            self.conn.send(xmpp.protocol.Message(self.to,text,self.type))
        else:
            '''Отправка сообщения в форме xhtml'''

            xhtml = '''
            <html xmlns='http://jabber.org/protocol/xhtml-im'>
            <body xml:lang='en-US' xmlns='http://www.w3.org/1999/xhtml'>
            %s
            </body></html>
            '''%extra
            
            self.conn.send("<message to='%s' type='%s'><body>%s</body>%s</message>"%(self.to,self.type,text,xhtml))

    def send_system(self,to,msg,type):
        '''Отправка системного сообщения. Статусы'''
        print to, msg, type
        self.conn.send(xmpp.protocol.Presence(to=to,status=msg,typ=type))

    def XMLescape(self, text):
        return xmpp.simplexml.XMLescape(text)

    def get_mes(self, conn, mess):
        def parse():
            if self.type_f:
                text = re.findall('^%s[\W]{0,2}[\s]{1,3}(.*?)$'%self.NICK,self.text)
            else:
                text = re.findall('^(.*?)$',self.text)
            self.DEBUG(text)
            if text:
                tmp = text[0].split(' ',1)
                if len(tmp) >= 2: cmd, args = tmp[0], tmp[1]
                elif len(tmp) == 1: cmd, args = tmp[0], ''
                return cmd, args

            else: return False, False
        def alias(cmd, args):
            text = ' '.join( (self.alias[cmd], args))
            tmp = text.split(' ',1)
            if len(tmp) >= 2: cmd, args = tmp[0], tmp[1]
            elif len(tmp) == 1: cmd, args = tmp[0], ''
            return cmd, args

        self.type=mess.getType()
        self.nick=mess.getFrom()
        self.text=mess.getBody()

        if self.type == 'groupchat':
            self.to = self.nick.getStripped()
            nick = self.nick.getResource()
            self.type_f = True
        elif self.type == 'chat' and self.nick.getDomain().startswith('conference.'):
            self.to = self.nick
            nick = self.nick.getResource()
            self.type_f = False
        elif self.type == 'chat':
            self.to = self.nick.getStripped()
            nick = self.nick.getNode()
            self.type_f = False

        '''    if (user in CONFERENCES) or (user in [i+u'/'+jid.getResource() for i in CONFERENCES]) or (user in IGNORE) or (user.getStripped() in IGNORE) or (type(text)!=type(u'')):
        '''
        self.DEBUG([self.nick,self.text,self.type])
        self.DEBUG(mess)
        if self.ignore.count(self.nick) or re.match('%s/%s'%(self.to,self.NICK),'%s/%s'%(self.to,nick) ):
            pass        
        elif self.text.startswith(self.NICK) or not self.type_f:
            cmd, args = parse()
            if self.alias.has_key(cmd):
                cmd,args = alias(cmd, args)
            if cmd:
                if self.commands.has_key(cmd):
                    self.commands[cmd](args)
                elif self.admin_commands.has_key(cmd):
                    if nick == self.admin.getNode() or self.to == str(self.admin).lower() :
                        self.admin_commands[cmd](self.nick,args)
                    else: self.send('%s~ nyaaa? Access denied...'%nick)
                else:  self.send('%s~ nyaaa? Type "help"...'%nick)
            else: self.send('%s~ nyaaa? Type "help"...'%nick)


    def send_iq(self,_type, to):
        self.conn.send(xmpp.protocol.Iq(to=to,typ=_type ,queryNS=xmpp.NS_VERSION))
    def get_iq(self,conn,mess):
        query = mess.getTag('query')
        client = '%s %s'%(query.getTagData('name'),query.getTagData('version') )
        os = query.getTagData('os')
        target = mess.getFrom().getResource()
        toversion  = '%s has client %s at %s'%(target, client, os)
        self.send(toversion)






'''
http://code.google.com/p/robocat/source/browse/trunk/start.py
http://www.linux.org.ru/view-message.jsp?msgid=2591531#2591657
'''

