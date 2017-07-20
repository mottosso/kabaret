'''


'''
from kabaret.gui.user_gui.user_panel import UserPanel
from kabaret.gui.user_gui.definition import Definition
from kabaret.gui.widgets.views import AbstractGuiView, QtGui, QtCore


class UserView(AbstractGuiView):
    def __init__(self, parent, client, app_name):
        super(UserView, self).__init__(parent, client, app_name)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        
        menubar = QtGui.QMenuBar(self)
        self.layout().addWidget(menubar)

        self.up = UserPanel(self, self.client)
        self.layout().addWidget(self.up)

        self._user_view_definitions = []
        self.load_definitions()
        view_menu = menubar.addMenu('Select View')
        for view_definition in self._user_view_definitions:
            view_menu.addAction(
                view_definition.title,
                lambda view_definition=view_definition: self.up.set_view(view_definition)
            )
            
    
    def load_definitions(self):
        all = _get_fake_definitions()
        self._user_view_definitions = [ Definition.from_dict(self.client, d) for d in all ]
        
    def on_connect(self):
        pass
                
def flow_curr_link(node_id):
    path = ['FLOW', 'Nav', 'current']
    ret = 'kabaret://Event?app_key=GUI&%s&etype=UPDATED&%s'%(
        '&'.join([ 'path=%s'%(i,) for i in path ]),
        '&'.join([ 'node_id=%s'%(i,) for i in node_id ]),
    )
    return ret

def _get_fake_user_asset_tasks_definition(asset_type, asset_name):
    def get_task(node_id, type):
        if type == 'HumanTask':
            actions = ('Update', 'Edit', 'Check', 'Request Review', 'Publish', 'Explore')
            statuses = ('OOP', 'NYS', 'INV', 'WIP', 'RVW', 'RTK', 'APP')
        elif type == 'BatchTask':
            actions = ('Update', 'Check', 'Explore')
            statuses = ('WAIT_INPUT', 'IN_PROGRESS', 'DONE')
        import random
        status = random.choice(statuses)
        color = {
            'OOP':'#555',
            'NYS':'#AAA',
            'INV':'#088', 
            'WIP':'#848',
            'RVW':'#A80',
            'RTK':'#808',
            'APP':'#080',
            'WAIT_INPUT': '#088',
            'IN_PROGRESS': '#848',
            'DONE':'#080',
        }.get(status, '#F00')
        path = '/'.join(node_id)
        full_node_id = ('Project', 'work', 'banks:Bank', asset_type+':'+asset_name)+node_id
        format = '<a style=\"color:#888; text-decoration:none;\" href="%s">%%s</a>'%(flow_curr_link(full_node_id),)
        widgets = [
            {'widget':'Tools', 'actions':actions},
            {'widget':'Pix', 'icon':('flow.icons.nodes', 'task')},
            {'widget':'Label', 'text':path, 'format':format},
            {'widget':'Choice', 'selected':status, 'choices':statuses, 'color':color},
        ]
        return {'widgets':widgets}
    
    id_to_type = {
        ('mod', 'work'): 'HumanTask',
        ('mod', 'notes'): 'BatchTask',
        ('setup', 'work'): 'HumanTask',
        ('setup', 'notes'): 'BatchTask',
    }
    ret = [
        {'widgets':[{'widget':'Label', 'text':asset_type.title()+' '+asset_name, 'format':'<hr><h2>%s</h2>'}]}
    ]
    for node_id in sorted(id_to_type.keys()):
        ret.append(get_task(node_id, id_to_type[node_id]))
    return ret

def _get_fake_user_tasks_definition():
    ret = []
    for actor in ('Toto', 'Titi', 'Tata'):
        ret.extend(_get_fake_user_asset_tasks_definition('actors', actor))
    for prop in ('Table', 'Chaise'):
        ret.extend(_get_fake_user_asset_tasks_definition('props', prop))
    for set in ('Maison',):
        ret.extend(_get_fake_user_asset_tasks_definition('sets', set))
    return ret

def _get_fake_definitions():
        all = []
        q = '<p>List <b>Tasks</b><p>assigned to me</p><b>and</b><p>connected <b>Tasks</b></p></p><p><b>Grouped by</b><p>Relation Name </p><b>and</b><p> id.</p></p>'
        all.append({'title': 'My Tasks', 'rows':_get_fake_user_tasks_definition(), 'query':q})
        all.extend([
            {
                'title': 'Some View',
                'rows': [
                    {
                        'widgets':[
                            {'widget':'Button', 'text':'A Button...', 'icon':('flow.icons.nodes', 'maya')},
                            {'widget':'Button', 'text':'Click me',    'icon':('flow.icons.nodes', 'file')},
                            {'widget':'Button', 'text':'node',        'icon':('flow.icons.nodes', 'node')},
                            {'widget':'Button', 'text':'asset',       'icon':('flow.icons.nodes', 'asset')},
                        ]
                    },
                    {
                        'widgets':[
                            {'widget':'Tree'},
                            {'widget':'Tree'},
                        ]
                    },
                ]
            },
            {
                'title': 'Assets',
                'rows': [
                    {
                        'widgets':[
                            {'widget':'Button', 'text':'A Button...', 'icon':('flow.icons.nodes', 'maya')},
                            {'widget':'Button', 'text':'asset',       'icon':('flow.icons.nodes', 'asset')},
                        ]
                    },
                    {
                        'widgets':[
                            {'widget':'Tree'},
                        ]
                    },
                ]
            },
            {
                'title': 'Shots',
                'rows': [
                    {
                        'widgets':[
                            {'widget':'Button', 'text':'A Button...', 'icon':('flow.icons.nodes', 'maya')},
                            {'widget':'Button', 'text':'Click me',    'icon':('flow.icons.nodes', 'file')},
                            {'widget':'Button', 'text':'node',        'icon':('flow.icons.nodes', 'node')},
                            {'widget':'Button', 'text':'asset',       'icon':('flow.icons.nodes', 'asset')},
                        ]
                    },
                    {
                        'widgets':[
                            {'widget':'Tree'},
                        ]
                    },
                ]
            },            
        ])
        return all
            
