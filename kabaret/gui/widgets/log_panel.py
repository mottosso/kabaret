
from . import QtCore, QtGui

class LogHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, *args, **kwargs):
        super(LogHighlighter, self).__init__(*args, **kwargs)
        
        highlight = QtGui.QTextCharFormat()
        highlight.setBackground(QtGui.QColor('#B0B000'))
        search = QtGui.QTextCharFormat()
        search.setBackground(QtGui.QColor('#804000'))
        self.formats = {
            'highlight':highlight,
            'search':search,
        }
        self.default_format = search
        
        self.hitexts = {}
    
    def remove_highlight(self, text):
        try:
            del self.hitexts[text]
        except KeyError:
            pass
        
    def add_highlight(self, text, format_name='highlight'):
        if '\n' in text:
            [ self.add_highlight(t) for t in text.split('\n') ]
            return
        format = self.formats.get(format_name, self.default_format)
        self.hitexts[text] = format
        self.rehighlight()
        
    def clear_highlights(self):
        self.hitexts.clear()
        self.rehighlight()
        
    def highlightBlock(self, text):
        try:
            text = str(text)
        except UnicodeEncodeError:
            text = unicode(text)
        for hitext, format in self.hitexts.items():
            tlen = len(hitext)
            last_index = 0
            while True:
                index = text.find(hitext, last_index)
                if index < 0:
                    break
                self.setFormat(index, tlen, format)
                last_index = index+tlen+1
            
class Filter(object):
    def __init__(self, name, active=True, group=None):
        super(Filter, self).__init__()
        self.name = name
        self.active = active
        self.group = group
        
    def allow(self, *args, **kwargs):
        return True


class LogPanel(QtGui.QWidget): 
    def __init__(self, parent):
        super(LogPanel, self).__init__(parent)

        self.filters = {} # {name: Filter}
        
        self.search_text = None
        
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)

        self.menu_bar = QtGui.QMenuBar(self)
        self.layout().addWidget(self.menu_bar)
        
        # ACTION MENU
        self.action_menu = self.menu_bar.addMenu('Log')
        self.action_menu_top_separator = self.action_menu.addSeparator()
        self.clear_action = self.action_menu.addAction('Clear', self.clear)
        self.toggle_linewrap_action = self.action_menu.addAction('Line wrap', self.toggle_linewrap)
        self.toggle_linewrap_action.setCheckable(True)
        
        # SEARCH MENU
        search_menu = self.menu_bar.addMenu("Search")
        self.search_action = search_menu.addAction('Search...', self._on_search_input)
        self.search_selected_action = search_menu.addAction('Search selected', self._on_search_selected)
        self.find_next_action = search_menu.addAction('Find previous', self._on_search_prev)
        self.find_previous_action = search_menu.addAction('Find next', self._on_search_next)
        search_menu.addSeparator()
        self.highlight_selected_action = search_menu.addAction('Highlight Selected', self._on_highlight_selected)
        self.clear_highlights_action = search_menu.addAction('Clear Highlights', self._on_clear_highlights)

        # FILTER MENU
        self.filter_menu = None
        
        self.t = QtGui.QTextEdit(self)
        self.t.setReadOnly(True)
        self.t.setLineWrapMode(self.t.NoWrap)
        self.t_highlighter = LogHighlighter(self.t.document())
        self.layout().addWidget(self.t)
        
        self.t.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(
            self.t, QtCore.SIGNAL('customContextMenuRequested(QPoint)'),
            self._on_t_rmb
        )

        self.toggle_linewrap_action.setChecked(self.t.lineWrapMode() != QtGui.QTextEdit.NoWrap)

    def add_action(self, text, callable, at_top=False):
        if at_top:
            before = self.action_menu.actions()[0]
        else:
            before = self.action_menu_top_separator
        action = QtGui.QAction(text, self.action_menu)
        action.triggered.connect(callable)
        self.action_menu.insertAction(before, action)
        return action
    
    def clear_filters(self):
        self.filters = {}
        
    def update_filter_menu(self):
        if not self.filters:
            if self.filter_menu is None:
                return
            self.filter_menu.clear()
            self.filter_menu.deleteLater()
            self.filter_menu = None
            return

        if self.filter_menu is None:
            self.filter_menu = self.menu_bar.addMenu('Filters')
        else:
            self.filter_menu.clear()
    
        comp_filters = lambda a,b: cmp((a.group, a.name), (b.group, b.name))
        sorted_filters = sorted(self.filters.values(), cmp=comp_filters)
        
        last_group = None
        got_one = False
        for filter in sorted_filters:
            if got_one and filter.group != last_group:
                self.filter_menu.addSeparator()
            last_group = filter.group
            action = self.filter_menu.addAction(
                filter.name, lambda filter_name=filter.name: self._on_toggle_filter(filter_name)
            )
            action.setCheckable(True)
            action.setChecked(filter.active)
            #if not filter.active:
            #    self._on_toggle_filter(filter.name)
    
            got_one = True
        
        
    def add_filter(self, filter, update_menu=True):
        self.filters[filter.name] = filter
        if update_menu:
            self.update_filter_menu()
    
    def remove_filter(self, filter_name):
        del self.filters[filter_name]
        
    def filter(self, *args, **kwargs):
        for filter in self.filters.values():
            if not filter.allow(*args, **kwargs):
                return False
        return True
    
    def _on_toggle_filter(self, filter_name):
        filter = self.filters[filter_name]
        filter.active = not filter.active
            
    def _on_t_rmb(self, pos):
        m = self.t.createStandardContextMenu()
        m.addSeparator()
        m.addAction(self.search_action)
        m.addAction(self.search_selected_action)
        m.addAction(self.find_next_action)
        m.addAction(self.find_previous_action)
        m.addSeparator()
        m.addAction(self.highlight_selected_action)
        m.addAction(self.clear_highlights_action)
        m.addSeparator()
        m.addAction(self.clear_action)
        m.addAction(self.toggle_linewrap_action)
        
        m.exec_(QtGui.QCursor.pos())

    def clear(self):
        self.t.clear()
    
    def append(self, text):
        self.t.append(text)
    
    def raw_append(self, text, color=None):
        self.t.moveCursor(QtGui.QTextCursor.End, )

        cf = self.t.currentCharFormat()
        if color is None:
            cf.clearForeground()
        else:
            cf.setForeground(QtGui.QColor(color))
        self.t.setCurrentCharFormat(cf)
        
        self.t.insertPlainText(text)
        
    def toggle_linewrap(self):
        if self.t.lineWrapMode() != QtGui.QTextEdit.NoWrap:
            self.t.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        else:
            self.t.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        self.toggle_linewrap_action.setChecked(
            self.t.lineWrapMode() != QtGui.QTextEdit.NoWrap
        )

    def get_selected_text(self, raise_message=None):
        if not self.t.textCursor().hasSelection():
            if raise_message is None:
                return None
            raise ValueError(raise_message)
        return str(self.t.textCursor().selectedText().replace(u'\u2029', '\n').replace(u'\u2028', '\n'))

    def _on_search_input(self):
        text, ok = QtGui.QInputDialog.getText(
            self.t,
            'Search in Listener View',
            'Search:', text=self.search_text and self.search_text or ''
        )
        if not ok:
            return
        if self.search_text:
            self.t_highlighter.remove_highlight(self.search_text)
        self.search_text = text
        self.t_highlighter.add_highlight(self.search_text, 'search')
        
    def _on_search_selected(self):
        if self.search_text:
            self.t_highlighter.remove_highlight(self.search_text)
        self.search_text = self.get_selected_text(raise_message='Nothing Selected in the Listener View.')
        self.t_highlighter.add_highlight(self.search_text, 'search')
        
    def _on_search_prev(self):
        self.search_text and self.t.find(
            self.search_text, 
            QtGui.QTextDocument.FindBackward
        )
    
    def _on_search_next(self):
        self.search_text and self.t.find(self.search_text)
        
    def _on_highlight_selected(self):
        text = self.get_selected_text()
        if text is None:
            return self._on_clear_highlights()
        self.t_highlighter.add_highlight(text)
    
    def _on_clear_highlights(self):
        self.t_highlighter.clear_highlights()
