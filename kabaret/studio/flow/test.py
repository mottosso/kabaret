'''

    

'''


def test_1():
    import sys 
    import mystudio.kabaret.apps.naming.examples.smks as naming
    #import kabaret.studio.naming.examples.smks as naming
    
    cases = CaseData()
    proj_case = cases.add_group('TestProj')
    proj_case['store'] = 'X:/KBR_STORE'
    banks = proj_case.add_group('banks')
    bank = banks.add_group('Bank')
    actors = bank.add_group('actors')
    bob = actors.add_group('Bob')
    if 1:
        mod = bob.add_group('mod')
        mod['start_date'] = datetime.date.today()-datetime.timedelta(40)
        mod['user_group'] = 'Mod'
        
    if 1:    
        setup = bob.add_group('setup')
        setup['start_date'] = datetime.date.today()-datetime.timedelta(30)
        setup['user_group'] = 'Setup'

    if 1:    
        shad_anim = bob.add_group('shad_anim')
        shad_anim['start_date'] = datetime.date.today()-datetime.timedelta(20)
        shad_anim['user_group'] = 'Setup'

    if 1:    
        split_for_anim = bob.add_group('split_for_anim')
        split_for_anim['start_date'] = datetime.date.today()-datetime.timedelta(10)
        split_for_anim['user_group'] = 'Setup'

    if 1:    
        shad_render = bob.add_group('shad_render')
        shad_render['start_date'] = datetime.date.today()-datetime.timedelta(0)
        shad_render['user_group'] = 'Shad'

    if 1:    
        split_for_render = bob.add_group('split_for_render')
        split_for_render['start_date'] = datetime.date.today()-datetime.timedelta(-10)
        split_for_render['user_group'] = 'Shad'
    
    proj_case = cases.add_group('TestOtherProj')
    proj_case['store'] = 'X:/KBR_STORE'
    banks = proj_case.add_group('banks')
    
    print cases.pformat()

    flow = ProjectFlow()
    flow.set_named_store(naming.StoreFolder.from_name('X:/KBR_STORE'))
    flow.get_root_class = lambda: Project
    #proj = Project(None, 'TestProj')
    #proj.set_case(cases['TestProj'])

    proj = flow.init_root(cases['TestProj'], 'TestProj')
    print proj
    print '#----- proj.store:', proj_case['store']
    print '#----- proj.naming:', proj.naming.get()
    bob = proj.banks['Bank'].actors['Bob']
    print '#---- ???', proj.banks['Bank'].alter_naming.update.get()
    print '#---- ???', bob.for_render.naming.get()
    print bob.for_render.filename.get()
    print bob.mod.filename.get()
    print 'for render is late?', bob.for_render.is_late.get()
    
            
    new_case = Project.create_case()
    import pprint
    pprint.pprint(new_case)
    

    # TEST GET RELATION
    print proj['banks']['Bank']#['actors']['Bob']
    
#    print proj.get_relative(['banks', 'Bank', 'actors', 'Bob'])
#    xx = proj.get_relative(['banks'])
#    print [ i for i in xx.get_relation_names() ]
#    print [ n for n in bob.get_relation_names() ]
    
    bob_uid = proj['banks']['Bank']['actors']['Bob'].uid()
    print 'Bob uid:', bob_uid
    print 'Bob from uid:', flow.get(bob_uid).path()
    root_uid = flow.get(node_uid=[]).uid()
    print 'Get Root from uid', root_uid, flow.get(node_uid=root_uid).path()


def test_x():
    '''
    find out the faster in try+except/is None/is not None
    result: is not None is faster
    '''
    class C(object):
        def __init__(self):
            self.x = None

    import time
    nb = 1000000
    c = C()

    t = time.time()
    for i in xrange(nb):
        pass
    print 'pass:', time.time()-t
    
    t = time.time()
    for i in xrange(nb):
        if c.x is not None:
            x = c.x
    print 'is not None:', time.time()-t
    
    t = time.time()
    for i in xrange(nb):
        if c.x is None:
            x = c.x
    print 'is None:', time.time()-t
    
    t = time.time()
    for i in xrange(nb):
        try:
            y = c.y
        except AttributeError:
            pass
    print 'try:', time.time()-t
    
def test_iter():
    '''
    find out the fastest iterator in tuple, list, set
    '''
    import time
    nb = 5000000

    iterable = tuple(range(nb))
    t = time.time()
    for i in iterable:
        pass
    print 'tuple:', time.time()-t

    iterable = list(range(nb))
    t = time.time()
    for i in iterable:
        pass
    print 'list:', time.time()-t

    iterable = set(range(nb))
    t = time.time()
    for i in iterable:
        pass
    print 'set:', time.time()-t

def test_plug_connection():
    class Param(Node):
        value = Plug('value')
        _plugs = [value]

        def plug_touched(self, plug_name):
            print 'Param value touched', self.get_plug_value(plug_name).path()

    class Computer(Node):
        param_1 = Plug('param_1')
        param_2 = Plug('param_2')
        result = Plug('result')
        _plugs = [param_1, param_2, result]

        def plug_touched(self, plug_name):
            print 'Param value touched', self.get_plug_value(plug_name).path()
            if plug_name in ('param_1', 'param_2'):
                self.result.touch()

        def compute(self, plug_name):
            print 'Computer plug compute', self.get_plug_value(plug_name).path()
            if plug_name == 'result':
                self.result.set(
                    self.param_1.get() + self.param_2.get()
                )

        def plug_cleaned(self, plug_name):
            print 'Computer plug cleaned', self.get_plug_value(plug_name).path()

    print '---- Init Nodes'
    c = Computer(None)
    s1 = Param(None, 's1')
    s2 = Param(None, 's2')

    print '---- Connecting'
    s2.value.add_source(s1.value)
    c.param_1.add_source(s2.value)

    print '---- SETTING param_2'
    c.param_2.set("/PARAM2/")

    print '---- SETTING S1'
    s1.value.set("/S1 A/")
    print "RESULT:"
    print c.result.get()

    print '---- SETTING S1'
    s1.value.set("/S1 B/")
    print "RESULT:"
    print c.result.get()

    print "RESULT:"
    print c.result.get()

def test_2():
    import mystudio.kabaret.apps.naming.examples.smks as naming

    case = Project.create_case()
    import pprint
    pprint.pprint(case)

    flow = ProjectFlow()
    flow.set_named_store(naming.StoreFolder.from_name('X:/KBR_STORE'))
    flow.get_root_class = lambda: Project

    proj = flow.init_root(case, 'TestProj')
    print proj

    P001 = proj.films['Film'].seqs['S01'].shots['P001']
    print P001.path()
    P001.prod_casting.uids.set([
        (proj.node_id, 'banks:Bank', 'actors:AnActor', 'split_for_anim'),
        (proj.node_id, 'banks:Bank', 'sets:TheSet', 'split_for_anim'),
        (proj.node_id, 'banks:Bank', 'props:OneProp', 'split_for_anim'),
    ])

    actor = flow.get((proj.node_id, 'banks:Bank', 'actors:AnActor'))
    print ">>>", actor.setup.up_naming.get(), "<<<"


    anim_id = (
        proj.node_id, 'films:Film', 'seqs:S01', 'shots:P001', 'anim'
    )
    anim = flow.get(anim_id)
    print anim
    print anim.parent().prod_casting.work_days.get()





if __name__ == '__main__':
    #test_plug_connection()
    test_2()
