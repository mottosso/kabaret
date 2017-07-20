'''



'''

from kabaret.flow.nodes.node import Node

from kabaret.flow.params.param import param_group
from kabaret.flow.params.case import CaseParam
from kabaret.flow.params.computed import ComputedParam
from kabaret.flow.params.trigger import TriggerParam


class Cast(Node):
    '''
    A Cast node is used by the Casting nodes to build up a set
    of interesting nodes.
    
    The Cast node must be a Child of the interesting node.
    '''
    with param_group('Casted By'):
        casting_uids = CaseParam().ui(editor='node_refs')
        castings = ComputedParam()

    def _configure(self):
        super(Cast, self)._configure()
        self._last_castings = None
        
    def get_casted(self):
        return [self.parent()]
    
    def add_casting(self, casting):
        casting_uid = casting.uid()
        casting_uids = self.casting_uids.get() or []
        if casting_uid not in casting_uids:
            self.casting_uids.set(
                casting_uids + [casting_uid]
            )

    def remove_casting(self, casting):
        casting_uid = casting.uid()
        casting_uids = self.casting_uids.get() or []
        try:
            casting_uids.remove(casting_uid)
        except ValueError:
            pass
        else:
            self.casting_uids.set(casting_uids)
    
    def param_touched(self, param_name):
        if param_name == 'casting_uids':
            self.castings.touch()
        else:
            super(Cast, self).param_touched(param_name)
            
    def compute(self, param_name):
        if param_name == 'castings':
            flow = self.flow()
            castings = []
            for uid in self.casting_uids.get() or []:
                try:
                    n = flow.get(uid)
                except:
                    continue
                castings.append(n)

            # Removes disconnected:
            for n in self._last_castings or []:
                if n not in castings:
                    n.remove_cast(self)
            
            # Add new connected:
            for n in castings:
                if n not in (self._last_castings or []):
                    n.add_cast(self)

            self.castings.set(castings)
            self._last_castings = list(castings)
        else:
            super(Cast, self).compute(param_name)

class Casting(Cast):
    '''
    A Casting node is used to build up a set of interesting nodes.
    
    It does so by storing a list of Cast node uids and generating
    a list of nodes.
    Each Cast node referenced knows in which Casting it is used
    and provide the node it casts.
    
    As a Casting node is also a Cast node, one can cast a casting
    in another one. This gives the ability to build complexe and
    hierarchical node groups.
    
    '''
    with param_group('Casting', 0):
        casted_uids = CaseParam().ui(editor='node_refs')
        casted = ComputedParam()
        clean_up = TriggerParam()
    
    def _configure(self):
        super(Casting, self)._configure()
        self._last_strict_casted = None
        
    def get_casted(self):
        return self.casted.get()
    
    def add_cast(self, cast):
        cast_uid = cast.uid()
        casted_uids = self.casted_uids.get() or []
        if cast_uid not in casted_uids:
            self.casted_uids.set(
                casted_uids + [cast_uid]
            )

    def remove_cast(self, cast):
        cast_uid = cast.uid()
        casted_uids = self.casted_uids.get() or []
        try:
            casted_uids.remove(cast_uid)
        except ValueError:
            pass
        else:
            self.casted_uids.set(casted_uids)

    def param_touched(self, param_name):
        if param_name == 'casted_uids':
            self.casted.touch()
        else:
            super(Casting, self).param_touched(param_name)

    def compute(self, param_name):
        if param_name == 'casted':
            flow = self.flow()
            casted = []
            strict_casted = []
            for uid in self.casted_uids.get() or []:
                node = flow.get(uid)                
                strict_casted.append(node)
                try:
                    casted.extend(node.get_casted())
                except AttributeError:
                    raise ValueError(
                        'The uid %r is not castable. Please add only Cast and Casting nodes'%(
                            uid,
                        )
                    )
            
            # Removes disconnected:
            for n in self._last_strict_casted or []:
                if n not in strict_casted:
                    n.remove_casting(self)
            
            # Add new connected:
            for n in strict_casted:
                if n not in (self._last_strict_casted or []):
                    n.add_casting(self)
            
            self.casted.set(casted)
            self._last_strict_casted = strict_casted
            
            # Touch the casting using me:
            castings = self.castings.get()
            print '##################', castings
            for casting in castings:
                casting.casted.touch()

        else:
            super(Casting, self).compute(param_name)

    def trigger(self, param_name):
        if param_name == 'clean_up':
            flow = self.flow()
            valid_uids = []
            for uid in self.casted_uids.get() or []:
                node = flow.get(uid)                
                try:
                    node.get_casted
                except AttributeError:
                    continue
                else:
                    valid_uids.append(uid)
                    
            self.casted_uids.set(sorted(valid_uids))
        
        else:
            super(Cast, self).trigger(param_name)


                