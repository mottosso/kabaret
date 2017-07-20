'''



'''

from kabaret.flow.nodes.node import Node
from kabaret.flow.params.param import Param
from kabaret.flow.params.case import CaseParam
from kabaret.flow.params.stream import StreamParam
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.params.trigger import TriggerParam
from kabaret.flow.relations.many import Many
from kabaret.flow.relations.one import One
from kabaret.flow.relations.child import Child

from . import notes
from . import casting

class User(Node):
    login = ComputedParam()
    
    first_name = CaseParam()
    last_name = CaseParam()
    mail = CaseParam()
    active = CaseParam().ui(editor='bool')

    teams = One(casting.Cast)
    
    def compute(self, param_name):
        if param_name == 'login':
            self.login.set(self.node_id)

#class TeamUser(Node):
#    user = CaseParam()
#    
#    login = Param()
#    first_name = Param()
#    last_name = Param()
#    mail = Param()
#    active = Param().ui(editor='bool')
#    
#    def param_touched(self, param_name):
#        if param_name == 'user':
#            self.login.disconnect()
#            self.first_name.disconnect()
#            self.last_name.disconnect()
#            self.mail.disconnect()
#            
#            user = self.user.get()
#            if user is not None:
#                self.login.add_source(user.login)
#                self.first_name.add_source(user.first_name)
#                self.last_name.add_source(user.last_name)
#                self.mail.add_source(user.mail)
            
class Team(casting.Casting):
    pass

