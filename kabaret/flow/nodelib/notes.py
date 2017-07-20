'''

    This module defines the Note and NoteThread nodes.
    
    Adding a NotheThread in any node will let the user
    add notes and receive email notification when a note
    is added.
    
    One must subclass NoteThread before using it and
    provide an implementation of the get_user_mail() method.
    (The default is to return the login itself, some smtp
    server might accept this)
    
'''

import datetime
import time

from ..nodes.node import Node
from ..params.param import Param, param_group
from ..params.case import CaseParam
from ..params.trigger import TriggerParam
from ..params.computed import ComputedParam

from ..relations.many import Many
from ..relations.child import Child


class Note(Node):
    ICON_NAME = 'note'
    
    authors = CaseParam([]).ui('Author(s)', editor='login_list', editor_options={
            'add':'Credit Me', 'remove':'Un-Credit Me', 'display_mode':'all'
        }
    )
    timestamp = CaseParam(time.time).ui('On', editor='timestamp')
    read_by = CaseParam([]).ui(
        editor='login_list', editor_options={
            'add':'Mark as read', 'remove':'Mark as unread'
        }
    )
    content = CaseParam('').ui(editor='text')
    
    notify_edited = TriggerParam()
    
    def trigger(self, param_name):
        if param_name == 'notify_edited':
            self.timestamp.set(time.time())
            self.read_by.set([])
            self.parent().send_notification(self, edited=True)
            
class NoteThread(Node):
    ICON_NAME = 'notethread'

    mail_notify = CaseParam([]).ui(
        editor='login_list', editor_options={
            'add':'Subscribe', 'remove':'Unsubscribe'
        }
    )
    notification_subject = ComputedParam()
    
    notes = CaseParam().ui(
        editor='relation_ids', 
        editor_options={'presets':['Infos', 'ToDo', 'Refs']}
    )
    thread = Many(Note, ids_param_name='notes')
    
    def get_user_mail(self, login):
        return login
    
    def get_smtp(self):
        '''
        Returns the smtp address and port to use to send mail notifications.
        Default is to return (None, None) which will cancel sending mails.
        
        NB: if get_notification_mailer_infos() returns gmail identification, you
        should return "smtp.gmail.com", 587 here
        '''
        return None, None 
    
    def get_notification_mailer_infos(self):
        '''
        Returns the mail address, login, password and reply address to use 
        to send notifications.
        Default is to return (None, None, None, None) which will cancel sending mails.
        
        If the returned reply address is None, the address will be used as reply address
        two.
        '''
        return None, None, None, None
    
    def send_notification(self, note, edited=False):
        get_user_mail = self.get_user_mail # for speed. (yes, I know..)
        mails = [ get_user_mail(login) for login in self.mail_notify.get() or [] ]
        mails = [ m for m in mails if m is not None ]
        
        if not mails:
            print 'NoteThread: no mail found for notification.'
            print ' -> mail canceled'
            return
        
        import smtplib
        from email.mime.text import MIMEText
        
        thread_uid_str = '/'.join(self.uid())
        mailer_address, mailer_login, mailer_pass, reply_to = self.get_notification_mailer_infos()
        reply_to = reply_to or mailer_address
        smtp, port = self.get_smtp()
        
        
        if None in (smtp, port, mailer_address, mailer_login, mailer_pass):
            print 'NoteThread: Could not find a valid configuration to send mail'
            print ' -> mail to', mails, 'canceled'
        else:
            if edited:
                txt = 'A note was edited in the thread %r:\n%r\n\n%s'%(
                    thread_uid_str, note.uid(), note.content.get()
                )
            else:
                txt = 'A new note was added to the thread %r:\n%r'%(thread_uid_str, note.uid())
            msg = MIMEText(txt)
            msg['Subject'] = self.notification_subject.get()
            msg['From'] = reply_to
            msg['To'] = ', '.join(mails)
            
            try:
                s = smtplib.SMTP(smtp, port)
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(mailer_login, mailer_pass)
                s.sendmail(mailer_address, mails, msg.as_string())
                s.quit()
            except:
                print 'NoteThread: error sending mail to', mails
                print 'Raising...'
                raise
    
    def compute(self, param_name):
        if param_name == 'notification_subject':
            proj_name = self.flow().project_name
            self.notification_subject.set(
                '[%s][Note] %s'%(proj_name, '/'.join(self.uid()))
            )
                        