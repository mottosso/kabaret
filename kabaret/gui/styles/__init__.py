
import platform

_STYLE_VALUES = {}

def apply_default_style(widget=None):
    if platform.system() not in ('Darwin', 'Linux'):
        from . import dark
        style = dark
    else:
        from . import neonative
        style = neonative
    style.apply(widget)

def get_style_value(group, name, default=None):
    global _STYLE_VALUES
    return _STYLE_VALUES.get(group, {}).get(name, default)

def get_style_values(group):
    global _STYLE_VALUES
    return dict(_STYLE_VALUES.get(group, {}))

def set_style_values(group, values):
    '''
    Update some values in the given style group.
    The values argument must be a dict.
    '''
    global _STYLE_VALUES
    _STYLE_VALUES.setdefault(group, {})
    _STYLE_VALUES[group].update(values)

def set_default_style_values():
    '''
    Initialize all style values to a decent default.
    '''
    set_style_values(
        'statuses',
        {
            'OOP':'#555',
            'NYS':'#AAA',
            'INV':'#088',
            'WAIT_INPUT':'#088',
            'WIP':'#848',
            'IN_PROGRESS':'#848',
            'RVW':'#A80',
            'RTK':'#808',
            'APP':'#080',
            'DONE':'#080',
            'FIN':'#080',
        }
    )
    
    set_style_values(
        'node_colors',
        {
            'CHILD': (200, 200, 200),
            'ONE': (128, 128, 200),
            'MANY': (128, 128, 200),
            'PROC': (128, 200, 200),
        }
    )
    
    set_style_values(
        'value_editor_stylesheets',
        {
            'COMPUTED': 'QWidget { border-color: #004444 }',
            'LINKED': 'QWidget { border-color: #000044 }',
            'EDITABLE': '',
            'VOLATILE': 'QWidget{ border-color: #555555 }',
            'EDITING': 'QWidget { border-color: #555522 }',
            'BUSY': 'QWidget { border-color: #775522 }',
            'ERROR': 'QWidget { color: #FF2222 }',
        }
    )
    
    set_style_values(
        'revision_colors',
        {
            'pending': '#550055',
            'my_pending': '#005555',
            'w': '#555555',
            'r': None,
        }
    )
    