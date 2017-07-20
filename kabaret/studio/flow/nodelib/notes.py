'''


'''

import kabaret.flow.nodelib.notes 

class NoteThread(kabaret.flow.nodelib.notes.NoteThread):
            
    def get_user_mail(self, login):
        # TODO: shouldn't we just access the FLOW app here
        # and use its methods? we're in the apphost process anyway...
        users_app = self.flow().get_users_app()
        return users_app.cmds.GetUserMail(login)
    
    def get_smtp(self):
        return "smtp.gmail.com", 587 
    
    def get_notification_mailer_infos(self):
        return 'noreplysmksdev@gmail.com', 'noreplysmksdev', 'supamonk09,', 'noreply@supamonk.com'
