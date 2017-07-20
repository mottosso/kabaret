

try:
    from collections import OrderedDict
except ImportError:
    from ._purepy_ordered_dict import OrderedDict
