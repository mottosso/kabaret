'''

    Test kabaret.flow.params.stream.StreamParam

'''

import unittest

from kabaret.flow import Flow
from kabaret.flow.nodes.node import Node
from kabaret.flow.params.param import Param
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.params.stream import StreamParam
from kabaret.flow.relations.child import Child


#
# Case mock up
#
class Case(object):
    def get_child_case(self, uid, type_names):
        return self
    
#
#    Defining Node to perform test on
#

class Something(Node):
    pass

class MyNode(Something):
    local_value = Param(0)
    stream = StreamParam(Something)
    value = ComputedParam()

    def param_touched(self, param_name):
        if param_name in ('stream', 'local_value'):
            self.value.touch()
            
    def compute(self, param_name):
        if param_name == 'value':
            ups = self.stream.get()
            if ups is None:
                self.value.set(self.local_value.get())
            else:
                try:
                    ups[0]
                except:
                    self.value.set(ups.value.get())
                else:
                    self.value.set(sum([ up.value.get() for up in ups ], 0))
 
class RootNode(Node):
    a = Child(MyNode)
    b = Child(MyNode)
    c = Child(MyNode)
    d = Child(MyNode)

#
#    Tests
#

class TestStreamParam(unittest.TestCase):
    def setUp(self):
        flow = Flow()
        flow.set_root_class(RootNode)
        self.root = flow.init_root(Case(), 'testing')
    
    def tearDown(self):
        pass
    
    def test_compute(self):
        self.root.a.value.set(1)
        self.root.b.value.set(20)
        self.root.c.value.set(300)
        self.root.d.value.set(4000)
        
        self.root.c.stream.add_source(self.root.a.stream)
        self.root.c.stream.add_source(self.root.b.stream)
        self.assertEqual(self.root.d.value.get(), 4000)

        self.root.d.stream.add_source(self.root.c.stream)
        self.assertEqual(self.root.d.value.get(), 21)


def main():
    unittest.main()
    
if __name__ == '__main__':
    main()