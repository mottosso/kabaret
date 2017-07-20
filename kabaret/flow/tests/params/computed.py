'''

    Test kabaret.flow.params.computed.ComputedParam

'''

import unittest

from kabaret.flow import Flow
from kabaret.flow.nodes.node import Node
from kabaret.flow.params.param import Param
from kabaret.flow.params.computed import ComputedParam

#
#    Defining Node to perform test on
#

class MyNode(Node):
    p1 = Param()
    p2 = Param()
    mult = ComputedParam()
    
    def param_touched(self, param_name):
        if param_name in ('p1', 'p2'):
            self.mult.touch()
            
    def compute(self, param_name):
        if param_name == 'mult':
            p1 = self.p1.get()
            if not isinstance(p1, int):
                raise Exception('Invalid value for param p1: must be int')
            p2 = self.p2.get()
            if not isinstance(p2, int):
                raise Exception('Invalid value for param p2: must be int')

            self.mult.set(p1*p2)


#
#    Tests
#

class TestComputedParam(unittest.TestCase):
    def setUp(self):
        flow = Flow()
        flow.set_root_class(MyNode)
        self.test_node = flow.init_root({}, 'testing')
    
    def tearDown(self):
        pass
    
    def test_compute(self):
        self.test_node.p1.set(2)
        self.test_node.p2.set(3)
        self.assertEqual(self.test_node.mult.get(), 6)

    def test_dirty_at_init(self):        
        flow = Flow()
        flow.set_root_class(MyNode)
        test_node = flow.init_root({}, 'test_dirty_at_init')
        self.assertTrue(test_node.mult.is_dirty())

    def test_dirty_after_dependency_set(self):        
        self.test_node.p1.set(4)
        self.assertTrue(self.test_node.mult.is_dirty())

    def test_clean_after_compute(self):
        self.test_node.p1.set(5)
        self.test_node.p2.set(6)
        self.assertTrue(self.test_node.mult.is_dirty())
        self.test_node.mult.get()        
        self.assertFalse(self.test_node.mult.is_dirty())

    def test_compute_twice(self):
        self.test_node.p1.set(3)
        self.test_node.p2.set(3)
        self.assertEqual(self.test_node.mult.get(), 9)

        self.test_node.p1.set(3)
        self.test_node.p2.set(4)
        self.assertEqual(self.test_node.mult.get(), 12)

    def test_compute_error(self):
        self.test_node.p1.set('1')
        self.test_node.mult.get()
        self.assertIsNot(self.test_node.mult.error, None)


def main():
    unittest.main()
    
if __name__ == '__main__':
    main()