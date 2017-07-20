
import warnings
import os, glob

_PATHS = {}
_CACHE = {}
_PIXCACHE = {}
_ICONCACHE = {}

class ResourcesError(Exception):
    pass

class NotFoundError(ResourcesError):
    pass

def add_folder(name, path):
    '''
    Register a folder to the search path.
    
    The name parameter will be used to retrieve files.
    
    The path parameter can be a file inside the folder
    to register, or the path of the folder itself.
    If a folder with the same name was previously added, the
    last one overrides the previous one.
    
    Every file in this folder will be available with:
        import smks.resources
        smks.resources.get(folder_name, file_name)
    (See get(), get_pixmap(), ...)
    
    Typical usage:
        - add resources from a python package:
            import kabaret.core.utils.resources
            kabaret.core.utils.resources.add_folder('icons', __file__)
        - use resources from this package:
            import kabaret.core.utils.resources
            kabaret.core.utils.resources.get('icons', 'maya')
            
    '''
    #TODO: make it work inside eggs?
    
    global _PATHS, _CACHE
    
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    _PATHS[name] = path
    
    # Remove cache for this folder name:
    for key in _CACHE.keys():
        if key[0] == name:
            del _CACHE[key]
        
    
def get(folder_name, file_name):
    '''
    Returns the file named file_name and registered
    under the folder folder_name. 
    '''
    global _PATHS, _CACHE

    cache_key = (folder_name, file_name)
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    
    try:
        path = _PATHS[folder_name]
    except KeyError:
        raise ResourcesError("Unknown resource folder "+repr(folder_name)+". (Did you install it first?)")
    
    files = glob.glob(os.path.join(path,file_name+('.' not in file_name and ".*" or "")))
    if not files:
        raise NotFoundError("Resource not found: "+`cache_key`)
    if len(files) > 1:
        warnings.warn("Several resources found for: "+`cache_key`)
    
    _CACHE[cache_key] = files[0] 
    return files[0]

def get_pixmap(folder_name, pixmap_name):
    '''
    Same as get, but returns a QPixmap
    '''
    global _PIXCACHE
    path = get(folder_name, pixmap_name)
    if path in _PIXCACHE:
        return _PIXCACHE[path]
    
    try:
        from kabaret.gui import import_qt
    except ImportError:
        raise ImportError('The kabaret.gui package must be available to create pixmap resources')
    QtCore, QtGui = import_qt()

    ret = QtGui.QPixmap(path)
    _PIXCACHE[path] = ret
    
    return ret

def get_icon(icon_ref, for_widget=None):
    '''
    If icon ref is an int, for_widget must not be None
    and its current QStyle will be used to return
    the Qt icon pointed by icon_ref.
    
    If icon_ref is a 2D tuple, it is used to call
    get_pixmap(*icon_ref)
    
    If icon_ref is a file path, an icon is created
    from this file.
    
    '''
    try:
        from kabaret.gui import import_qt
    except ImportError:
        raise ImportError('The kabaret.gui package must be available to create icon resources')
    QtCore, QtGui = import_qt()
        
    if isinstance(icon_ref, int):
        style = for_widget.style()
        return style.standardIcon(icon_ref)

    global _ICONCACHE
    if icon_ref in _ICONCACHE:
        return _ICONCACHE[icon_ref]

    pix = None
    try:
        pix = get_pixmap(*icon_ref)
    except:
        try:
            if os.path.isfile(icon_ref):
                pix = QtGui.QPixmap(icon_ref)
        except TypeError:
            pass
        
    if pix is None:
        raise NotFoundError('Cannot find icon for %r'%(icon_ref,))
    
    icon = QtGui.QIcon(pix)
    _ICONCACHE[icon_ref] = icon 
    return icon
