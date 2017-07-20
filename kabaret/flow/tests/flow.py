'''

    Test the overall behavior.

'''

import unittest

from kabaret.flow.nodes.node import Node
from kabaret.flow.params.case import CaseParam
from kabaret.flow.params.param import Param
from kabaret.flow.relations.child import Child
from kabaret.flow.relations.many import Many


#
#    Defining Node to perform test on
#

class ChildNode(Node):
    child_param = Param()
    
    def configure(self, value):
        self.child_param.set(value)
        
class CasedNode(Node):
    node_param = Param()
    node_case_param = CaseParam(default='Case Param Default')
    
    c1 = Child(ChildNode).configure('Param in c1')
    c2 = Child(ChildNode).configure('Param in c2')

class NodeWithRelations(Node):
    nwr_param = Param()
    
    contained = Many(CasedNode)


#
#    Tests
#

class TestCaseData(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_create_case(self):
        pass




def main():
    unittest.main()
    
if __name__ == '__main__':
    main()