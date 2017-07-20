'''


'''

from collections import defaultdict

import kabaret.core.utils.resources

from kabaret.gui import import_qt
QtCore, QtGui = import_qt()


class TreeItem(object):
    '''
    The base class for all items in a TreeModel.
    Loads it children on a call to load_children() or find()
    '''
        
    def __init__(self, model, item_id, parent=None, color=QtGui.QColor(255, 255, 255)):
        super(TreeItem, self).__init__()
        self._parent = parent
        self._model = model
        self._item_id = item_id
        self._children = []
        self._color = color

        self._waiter = None
        self._children_loaded = False

    def _reset(self):
        '''
        Resets the item to its init state.
        This is triggered by the model on its
        root item.
        '''
        self._children = []
        self._waiter = None
        self._children_loaded = False
        
    def is_indicator(self):
        return False
    
    def appendChild(self, item):
        self._children.append(item)
      
    def clearChildren(self):
        self._children = []
    
    def child(self, row):
        return self._children[row]
    
    def childCount(self):
        self.load_children()
        return len(self._children)
    
    def hasChildren(self):
        if not self._children_loaded:
            return True
        return self._children and True or False
    
    def children(self):
        '''
        Returns a list with all children.
        (changes to the list will not affect this item)
        '''
        return list(self._children)
    
    def columnCount(self):
        raise NotImplementedError
    
    def label(self, column):
        raise NotImplementedError
      
    def item_id(self):
        '''
        Returns the id represented by this TreeItem (internal object)
        '''
        return self._item_id
    
    def mime_data(self, column):
        '''
        Return a dict like {mime_type: mime_string_data} for this 
        column of this item.
        Default implementation is to return something like this:
        {
            'text/plain': <label of given column>
        }
        
        NB: do not use the '\n' in the string data at it is used
        as a separator by the dropTarget.
        '''
        return {
            'text/plain': self.label(column)
        }
    
    def model(self):
        return self._model
    
    def parent(self):
        return self._parent
    
    def color(self):
        '''
        Returns the QColor of this item.
        '''
        return self._color
    
    def pix_ref(self, column):
        '''
        Returns the ref to a pixmap in the kabaret
        resources (see kabaret.utils.resources.get_pixmap())
        
        or None for no icon on the item.
        '''
        return None
    
    def row(self):
        if self._parent:
            return self._parent._children.index(self)
        return 0

    def load_children(self, blocking=False):
        '''
        Call when the children of this Item are requested.
        Subclasses must override this and call the base 
        implementation before doing anything: if the return 
        value is True, children can be added. If the return
        value is False, children were already loaded.
        
        Once the children are loaded, a call to children_loaded()
        must be done.
        If blocking is False, this method can return without
        calling children_loaded() (but it must be called at some point).
        If blocking is True, this method must load the children
        and call children_loaded() before returning.
        
        Don't forget to use beginInsertRows() and endInsertRows()
        on the model when you add the child Items to this one
        (with appendChild)
        '''
        if self._children_loaded:
            return False

        self._children_loaded = True
        self._show_loading()
        return True
    
    def children_loaded(self):
        self._hide_loading()
        
    def _show_loading(self):
        self._waiter = LoadingIndicatorItem(self)

    def _hide_loading(self):
        self._waiter and self._waiter.remove()

    def find(self, sub_id_path):
        '''
        Tries to find a sub item pointed by the list of
        item_id 'sub_id_path'.
        
        If found, True and the Item are returned.
        If not, False and the deepest matching item are returned.
        '''
        self.load_children(blocking=True)
        
        if not sub_id_path:
            return True, self
        
        for c in self._children:
            if c._item_id == sub_id_path[0]:
                return c.find(sub_id_path[1:])

        return False, self


class LoadingIndicatorItem(TreeItem):
    def __init__(self, loading_item):
        super(LoadingIndicatorItem, self).__init__(
            loading_item._model, '_Loading_', loading_item, color=QtGui.QColor(128, 128, 128)
        )
        self._removed = False
        
        index = loading_item._model.createIndex(loading_item.row(), 0, loading_item)
        parent_index = len(loading_item._children)
        
        loading_item._model.beginInsertRows(index, parent_index, parent_index+1)
        loading_item.appendChild(self)
        self._model.endInsertRows()

    def remove(self):
        if self._removed:
            return
        self._removed = True
        index = self._model.createIndex(self._parent.row(), 0, self._parent)
        parent_index = self.row()
        
        self._model.beginRemoveRows(index, parent_index, parent_index)
        self._parent._children.remove(self)
        self._parent.waiter = None
        self._model.endRemoveRows()

    def is_indicator(self):
        return True    

    def label(self, column):
        return 'Loading'

    def hasChildren(self):
        return False
    
class TreeModel(QtCore.QAbstractItemModel):
    '''
    A model for n-tree data (using TreeItem instances).
    '''
    _ICON_CACHE = {} # local pix cache.
    
    def __init__(self, parent=None, column_labels=[]):
        super(TreeModel, self).__init__(parent)
        self._root = None
        self._column_labels = column_labels
        
    def clear(self):
        if self._root.hasChildren():
            self.reset()
            self._root.clearChildren()
    
    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self._root.columnCount()
    
    def set_root(self, root):
        self._root = root
        
    def root(self):
        return self._root
    
    def reset(self):
        self.beginResetModel()
        self._root._reset()
        self.endResetModel()

    def data(self, index, role):
        if not index.isValid():
            return None
    
        if role == QtCore.Qt.DisplayRole:
            return index.internalPointer().label(index.column())
        elif role == QtCore.Qt.ForegroundRole:
            return index.internalPointer().color()
        elif role == QtCore.Qt.DecorationRole:
            pix_ref = index.internalPointer().pix_ref(index.column())
            # This fails cause of a bug in PySide 1.0.0:
            #return pix_ref and self.get_icon(*pix_ref) or None
            # So:
            if pix_ref:
                icon =  self.get_icon(*pix_ref) # need to assign the icon!!!
                return icon 
        return None
    
    def get_icon(self, *pix_ref):
        icon = None
        try:
            icon = self.__class__._ICON_CACHE[pix_ref]
            try:
                if icon:
                    pass
            except RuntimeError:
                # this happens with PySide 1.0.0
                del self.__class__._ICON_CACHE[pix_ref]
                raise
        except:
            try:
                icon = kabaret.core.utils.resources.get_icon(pix_ref)
            except kabaret.core.utils.resources.NotFoundError:
                icon = None
            self.__class__._ICON_CACHE[pix_ref] = icon
            
        return icon
        
    def mimeData(self, indexes):
        d = defaultdict(list) 
        for index in indexes:
            if not index.isValid():
                continue
            for k, v in index.internalPointer().mime_data(index.column()).items():
                d[k].append(v)
        
        md = QtCore.QMimeData()
        for k, v in d.items():
            md.setData(k, '\n'.join(v))
        
        return md
    
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if index.internalPointer().is_indicator():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
    
    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal:
            return None
        if role == QtCore.Qt.DisplayRole:
            try:
                return self._column_labels[section]
            except IndexError:
                return None
            except TypeError:
                return '!?! bad column names'
        return None
    
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        
        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()
        
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
    
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        
        if parentItem == self._root or parentItem is None:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)
        
    def hasChildren(self, parent_index):
        if not parent_index.isValid():
            return True
        return parent_index.internalPointer().hasChildren()
        
    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()
        
        return parentItem.childCount()


