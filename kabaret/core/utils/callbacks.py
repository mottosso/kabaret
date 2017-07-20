

raise RuntimeError('The kabaret.core.utils module is obsolete.')




import weakref


class NoneRef(object):
    def __call__(self):
        return None

class WeakMethod(object):
    def __init__(self, method):
        self._method = method.im_func
        self._object = weakref.ref(method.im_self)
    
    def __nonzero__(self):
        return self._object() is not None
        
    def __call__(self, *args):
        obj = self._object()
        if obj:
            return self._method(obj, *args)

def weak_ref(o):
    ref = NoneRef()
    if object:
        if hasattr(o, "im_func"):
            ref = WeakMethod(o)
        else:
            ref = weakref.ref(o)
    
    return ref
