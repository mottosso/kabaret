


def make_relative_id(from_id, to_id):
    f = list(from_id)
    t = list(to_id)
    
    #TODO: this is ugly and should not be useful
    if f[0] == 'FLOW':
        f.pop(0)
    if t[0] == 'FLOW':
        t.pop(0)

    while f and t and f[0] == t[0]:
        f.pop(0)
        t.pop(0)
    
    if f:
        ret = len(f)*('..',)+tuple(t)
    elif t:
        ret = ('.',)+tuple(t)
    else:
        ret = to_id

    return ret