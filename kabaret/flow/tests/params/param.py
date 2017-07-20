'''

    Test kabaret.flow.params.ComputedParam

'''

import unittest

from kabaret.flow import Flow
from kabaret.flow.case import CaseData
from kabaret.flow.nodes.node import Node
from kabaret.flow.params.param import Param
from kabaret.flow.relations.child import Child


#
#    Defining Node to perform test on
#

class MyNode(Node):
    p1 = Param()
    p2 = Param()
    
    def param_touched(self, param_name):
        if param_name == 'p1':
            self.p2.touch()
    

class ComplexNode(Node):
    p1 = Param()
    p2 = Param()
    
    def param_touched(self, param_name):
        if param_name == 'p1':
            self.p2.touch()

    child1 = Child(MyNode)
    child2 = Child(MyNode)
    
#
#    Tests
#

class TestParam(unittest.TestCase):        
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def create_flow_root(self):
        flow = Flow()
        flow.set_root_class(ComplexNode)
        return flow.init_root(CaseData(('testing',), ComplexNode.type_names()), 'testing')
        
    def test_dirty_at_init(self):
        root_node = self.create_flow_root()
        self.assertTrue(root_node.p1.is_dirty())
    
    def test_clean_after_set(self):
        root_node = self.create_flow_root()
        root_node.p1.set(9)
        self.assertFalse(root_node.p1.is_dirty())
    
    def test_rank_on_local_connection(self):
        root_node = self.create_flow_root()
        
        self.assertEqual(root_node.p2.rank(), 0)
        self.assertEqual(root_node.rank(), 0)
        
        root_node.p2.add_source(root_node.p1)
        
        # Local connections does not inc rank:
        self.assertEqual(root_node.p2.rank(), 0)
        self.assertEqual(root_node.rank(), 0)
        
    def test_rank_on_sibbling_connection(self):
        root_node = self.create_flow_root()
        
        c1 = root_node.child1
        c2 = root_node.child2
        
        self.assertEqual(c1.rank(), 0)
        self.assertEqual(c2.rank(), 0)
        
        c2.p2.add_source(c1.p1)
        
        # Sibbling connections does inc rank:
        self.assertEqual(c2.p2.rank(), 1)
        self.assertEqual(c2.p1.rank(), 0)
        self.assertEqual(c2.rank(), 1)
        
        self.assertEqual(c1.p2.rank(), 0)
        self.assertEqual(c1.p1.rank(), 0)
        self.assertEqual(c1.rank(), 0)
    
    def test_dirty_after_add_source(self):
        root_node = self.create_flow_root()
        
        c1 = root_node.child1
        c2 = root_node.child2

        c1.p1.set(1)
        c2.p2.set(2)
        
        self.assertFalse(c1.p1.is_dirty())
        self.assertFalse(c2.p2.is_dirty())

        c2.p2.add_source(c1.p1)

        self.assertFalse(c1.p1.is_dirty())
        self.assertTrue(c2.p2.is_dirty())

    def test_disconnect_after_set(self):
        root_node = self.create_flow_root()
        
        c1 = root_node.child1
        c2 = root_node.child2

        c1.p1.set(18)
        c2.p2.add_source(c1.p1)

        self.assertEqual(c2.p2.get(), 18)

        c2.p2.set(8)
        self.assertFalse(c2.p2.upstreams)
        self.assertEqual(c2.p2.get(), 8)


def main():
    unittest.main()
    
if __name__ == '__main__':
    main()
    