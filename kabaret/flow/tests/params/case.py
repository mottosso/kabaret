'''

    Test kabaret.flow.params.computed.ComputedParam

'''

import unittest

from kabaret.flow import Flow
from kabaret.flow.case import CaseData
from kabaret.flow.nodes.node import Node
from kabaret.flow.params.param import Param
from kabaret.flow.params.case import CaseParam
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.relations.many import Many
from kabaret.flow.relations.child import Child

#
#    Defining Node to perform test on
#

class MyCaseData(CaseData):
    '''
    This CaseData class fakes entries for test purpose.
    '''
    def get_mandatory_doc(self):
        # Get the empty doc:
        doc = super(MyCaseData, self).get_mandatory_doc()
        
        # Fill with value depending on the node id:

        if doc['_id'] == ('testing', 'related:TestDefaultCaseId') and self.sub_path == ():
            doc['p2'] = 3
        
        elif doc['_id'] == ('testing', 'related:AnotherCaseId') and self.sub_path == ():
            doc['p2'] = 4
        
        elif doc['_id'] == ('testing', 'related:MissingCaseId') and self.sub_path == ():
            #NB: ('testing', 'related', 'MissingCaseId') deliberately missing
            pass
        
        elif doc['_id'] == ('testing', 'related_with_children:CompoNodeId') and self.sub_path == ():
            doc.update({
                'p1': 5,
                'my_child': {
                    'p2': 6
                }
            })
            
        # Return the doc
        return doc 
    

class MyNode(Node):
    p1 = Param()
    p2 = CaseParam()
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

class MyComposedNode(Node):
    p1 = CaseParam()
    
    my_child = Child(MyNode)
    
class RootNode(Node):
    related = Many(MyNode, 'TestDefaultCaseId')
    related_with_children = Many(MyComposedNode, 'CompoNodeId')
    
#
#    Tests
#

class TestCaseParam(unittest.TestCase):
    def setUp(self):
        flow = Flow()
        flow.set_root_class(RootNode)
        self.root_case = MyCaseData(('testing',), RootNode.type_names())
        self.test_node = flow.init_root(self.root_case, 'testing')
        
        # This must match the data supported in MyCaseData.get_mandatory_doc()
        p = self.test_node.get_relation('related').get_ids_param_value(self.test_node)
        p.set(('TestDefaultCaseId','AnotherCaseId'))
        
    def tearDown(self):
        pass

    def test_get_related_ids(self):
        case_ids = self.test_node.related.get_related_ids()
        self.assertEqual(case_ids, ('TestDefaultCaseId', 'AnotherCaseId'))
        
    def test_get_case(self):
        related_node = self.test_node.related['TestDefaultCaseId']
        
        self.assertEqual(related_node.p1.get(), None)
        related_node.p1.set(2)
        self.assertEqual(related_node.p1.get(), 2)
        self.assertEqual(related_node.p2.get(), 3)
        self.assertEqual(related_node.mult.get(), 6)

    def test_get_missing_case(self):
        related_node = self.test_node.related['MissingCaseId']
        self.assertEqual(related_node.p2.get(), None)

    def test_get_deep_case(self):
        node = self.test_node.related_with_children['CompoNodeId']
        self.assertEqual(node.p1.get(), 5)
        self.assertEqual(node.my_child.p2.get(), 6)


def main():
    unittest.main()
    
if __name__ == '__main__':
    main()