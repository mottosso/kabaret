'''

    kabaret.gui.widgets.value_editor package.
    
    Provide an editor factory that generates widgets editing
    python values.
    
'''

from kabaret.core.events.event import Event
from kabaret.gui.styles import get_style_value

_FACTORY = None # Global EditorFactory, instancied and accessible by get_global_factory()

class ValueController(object):
    '''
    A ValueController is used by each editor to apply
    modification and receive updates.
    '''
    def __init__(self, client, value_id, app_key=''):
        '''
        If app_key is given, it must match the app 
        managing the editor's value_id.
        
        This is needed only to avoid clashes when
        two app may have values with the sams id,
        but should be used anyway since it speeds
        up the event dispatching.
                
        '''        
        super(ValueController, self).__init__()
        
        self.client = client
        self.app_key = app_key
        self.value_id = value_id
        self._set_value_id = None
        self.editor = None
    
    def set_editor(self, editor):
        '''
        This connects the controller to the given
        editor and make it start listening for
        events the value_id.
        '''
        if self.editor is not None:
            raise Exception('This controller is already tied to an editor.')
        self.editor = editor
        self._start_listening()
    
    def override_set_value_id(self, target_value_id):
        '''
        Some(weird)times the controller watching a value
        should set another one.
        This tells the controler to do so by setting the
        value 'target_value_id' instead of the watched 'value_id'.
        '''
        self._set_value_id = target_value_id
        
    def _start_listening(self):
        '''
        Start listening for events related to 
        this controller's value_id.
        '''
        self.client.add_event_handler(
            self.value_invalidated, 
            'FLOW', 
            self.value_id, 
            etype=Event.TYPE.INVALIDATED
        )
    
    def stop_listening(self):
        '''
        Stop listening for events related to 
        this controller's value_id.
        
        This must be called before the controller
        is destroyed.
        '''
        self.client.remove_event_handler(
            self.value_invalidated
        )

    def set_value(self, value):
        '''
        Subclasses must implement this to alter the value.
        '''
        raise NotImplementedError
    
    def value_invalidated(self, event):
        '''
        Subclasses must implement this to fetch the 
        updated value and update the editor.
        
        The event parameter is the kabaret.core.events.event.Event
        that triggered this call
        '''
        raise NotImplementedError


class _StyleSheetProvider(object):
    def __init__(self):
        super(_StyleSheetProvider, self).__init__()
        self._cached = {}
    
    def get(self, name):
        try:
            return self._cached[name]
        except KeyError:
            self._cached[name] = get_style_value(
                'value_editor_stylesheets', name
            )
            return self._cached[name]
        
    def COMPUTED(self):
        return self.get('COMPUTED')
    
    def LINKED(self):
        return self.get('LINKED')

    def EDITABLE(self):
        return self.get('EDITABLE')

    def VOLATILE(self):
        return self.get('VOLATILE')

    def EDITING(self):
        return self.get('EDITING')

    def BUSY(self):
        return self.get('BUSY')

    def ERROR(self):
        return self.get('ERROR')


class ValueEditorMixin(object):
    '''
    The ValueEditorMixin is a class to inherit along with
    a widget to create an editor.
    '''
    STYLE_SHEETS = _StyleSheetProvider()
    
    def __init__(self, controller, options):
        super(ValueEditorMixin, self).__init__()
        self._controller = controller
        self._options = options
        
        self._init_style_sheet = self.STYLE_SHEETS.EDITABLE()
        self._init_read_only = True
        self._last_value_set = None
        self._error_msg = None

        self._controller.set_editor(self)
        
    def _ui_widgets(self):
        '''
        Subclass must implement this and return 
        a list of widget to style.
        Default is to return [self].
        '''
        return [self]

    def set_label(self, label=None):
        '''
        Sets the label of the editor.
        Most of the value editors will ignore
        this.
        '''
        return

    def get_value(self):
        '''
        Subclass must implement this method and return
        the value currently displayed in this editor.
        '''
        raise NotImplementedError

    def set_value(self, value):
        '''
        Subclass should override this to display
        the given value in this editor. 
        Suclass must call this implementation in 
        their override.
        '''
        self._last_value_set = value

    def update_value(self, new_value):
        '''
        Called when the value changed externally.
        The editor style is cleared to default.
        '''
        self.set_value(new_value)
        self.set_clean()
        
    def edit_started(self):
        '''
        Shows the editor in an 'editing' style.
        '''
        for w in self._ui_widgets():
            w.setStyleSheet(self.STYLE_SHEETS.EDITING())
    
    def edit_finished(self):
        '''
        Applies the displayed value to the value
        and show a 'busy' style (waiting for a
        call to update_value() that validates the
        edition).
        '''
        if self.get_value() == self._last_value_set:
            self.set_clean()
            return
        self._controller.set_value(self.get_value())
        self.set_busy()
    
    def set_linked(self):
        '''
        Change the default style of this editor
        to 'linked'.
        
        The linked style depicts a dependency on the
        edited value that prevents the editor to change
        it.
        
        This mode sets the editor as read only.
        
        '''
        self._init_read_only = True
        self._set_read_only(True)
        for w in self._ui_widgets():
            w.setStyleSheet(self.STYLE_SHEETS.LINKED())
        self._init_style_sheet = self.STYLE_SHEETS.LINKED()
    
    def set_computed(self):
        '''
        Change the default style of this editor
        to 'computed'.
        
        The computed style indicated that the value 
        is the result of a computation rather than user
        input.
        
        This mode sets the editor as read only.
        
        '''
        self._init_read_only = True
        self._set_read_only(True)
        for w in self._ui_widgets():
            w.setStyleSheet(self.STYLE_SHEETS.COMPUTED())
        self._init_style_sheet = self.STYLE_SHEETS.COMPUTED()

    def set_editable(self):
        '''
        Change the default style of this editor
        to 'editable'.
        
        This style indicated that the value can be altered
        by user input.
        
        '''
        self._init_read_only = False
        for w in self._ui_widgets():
            w.setStyleSheet(self.STYLE_SHEETS.EDITABLE())
        self._init_style_sheet = self.STYLE_SHEETS.EDITABLE()
        self._set_edit_connections()
    
    def set_volatile(self):
        '''
        Change the default style of this editor
        to 'volatile'.
        
        This style indicated that the value can be altered
        by user input but will not be persisted.
                
        '''
        self._init_read_only = False
        for w in self._ui_widgets():
            w.setStyleSheet(self.STYLE_SHEETS.VOLATILE())
        self._init_style_sheet = self.STYLE_SHEETS.VOLATILE()
        self._set_edit_connections()
        
    def _set_edit_connections(self):
        '''
        Subclasses must implement this method
        to setup connections that will trigger
        state change of the editor (like edit_stated()
        or edit_finished())
        '''        
        raise NotImplementedError
    
    def _set_read_only(self, b):
        '''
        Subclasses may need to override this
        and set custom states on widget (using
        setEnabled instead of setReadOnly for
        example)
        
        The default is to call setReadOnly(b)
        on all widgets returned by _ui_widgets().
        
        '''
        for w in self._ui_widgets():
            w.setReadOnly(b)
    
    def set_busy(self):
        '''
        Activates the 'busy' state indicating
        that a new value has been posted 
        but the update is still waited.
        '''
        self._set_read_only(True)
        for w in self._ui_widgets():
            w.setStyleSheet(self.STYLE_SHEETS.BUSY())

    def set_clean(self):
        '''
        Activates the 'clean' state indicating that
        the displayed value matches the actual value.
        '''
        self._set_read_only(self._init_read_only)
        for w in self._ui_widgets():
            w.setStyleSheet(self._init_style_sheet)

    def set_error(self, error_msg=None):
        '''
        Activates the 'error' state indicating that
        the something went wrong as described in the
        given error message.
        '''
        self._error_msg = error_msg
        if self._error_msg:
            for w in self._ui_widgets():
                w.setStyleSheet(self._init_style_sheet+'\n'+self.STYLE_SHEETS.ERROR())
        else:
            for w in self._ui_widgets():
                w.setStyleSheet(self._init_style_sheet)
            
    def set_tooltip(self, text):
        '''
        Sets the tooltip text for the value.
        
        Default is to use setToolTip on all
        the widgets returned by _ui_widgets().
        '''
        for w in self._ui_widgets():
            w.setToolTip(text)


class EditorFactory(object):
    '''
    The EditorFactory can instantiate registered value editors.
    
    You should not need to create an EditorFactory and may want
    to use the get_global_factory() function to access the global one.
    '''
    
    def __init__(self):
        super(EditorFactory, self).__init__()
        self._default_type = None
        self._editor_types = {}
    
    def keys(self):
        '''
        Returns the list of known value editor type.
        (a.k.a. the value suitable for the 'key' argument of
        the create method)
        '''
        return sorted(self._editor_types.keys())
    
    def ensured_registered(self, **key_to_editor_type):
        '''
        Registers the given editor types to the given
        keys only if none has been registered yet for
        the key.
        See also register()
        '''
        for key, editor_type in key_to_editor_type.items():
            if self._editor_types.get(key) is None:
                self._editor_types[key] = editor_type
    
    def register_default(self, editor_type):
        '''
        Override the default editor_type used when create()
        is asked for an unknown editor_type.
        '''
        self._default_type = editor_type
        
    def register(self, key, editor_type, is_default=False):
        '''
        Adds or modify the class to instantiate when the create
        method is called with this key.
        
        If is_default is True, a request for an unregistered 
        value editor key will creat this type.
        
        '''
        self._editor_types[key] = editor_type
        if is_default:
            self._default_type = editor_type
            
    def create(self, parent, key, controller, options=None):
        '''
        Creates a value editor of the type registered under 'key',
        sets it up to work with the given controller and returns it.
        '''
        editor_type = self._editor_types.get(key, self._default_type)
        if editor_type is None:
            raise Exception(
                'The EditorFactory could not find an editor type for %r and no default type was set.'%(
                    key,
                )
            )
        
        return editor_type(parent, controller, options or {})

def get_global_factory():
    '''
    Returns the global EditorFactory.
    '''
    global _FACTORY 
    if _FACTORY is None:
        _FACTORY = EditorFactory()
        from . import editors
        _FACTORY.ensured_registered(
            int=editors.IntValueEditor,
            strlist=editors.StrListValueEditor,
            date=editors.DatetimeValueEditor,
            bool=editors.BoolValueEditor,
            text=editors.TextValueEditor,
            trigger=editors.ButtonValueEditor,
            timestamp=editors.TimestampValueEditor,
            percent=editors.PercentValueEditor,
            pie=editors.PieValueEditor,
            status_sumary=editors.PieStatusesEditor,
            choice=editors.ChoiceEditor,
            choices_for=editors.ChoicesForEditor,
            login_list=editors.LoginListValueEditor,
            thumbnail=editors.ThumbnailValueEditor,
        )
        _FACTORY.register_default(editors.GenericValueEditor)
        
    return _FACTORY
