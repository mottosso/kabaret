'''
    Copyright (c) Supamonks Studio and individual contributors.
    All rights reserved.

    This file is part of kabaret, a python Digital Creation Framework.

    Kabaret is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
        
    Redistributions in binary form must reproduce the above copyright 
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
    
    Kabaret is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.
    
    You should have received a copy of the GNU Lesser General Public License
    along with kabaret.  If not, see <http://www.gnu.org/licenses/>

--

    The kabaret.flow.case package.
    Defines the base class CaseData for case data handling.
    
'''

import os, pprint, glob, time


class CaseData(object):
    '''
    The CaseData class is used by the node instances
    to access the CaseParam data of a case.
    
    The Flow holding your nodes needs a CaseData in order
    to initialize its root node.
    The root children nodes will use the CaseData from
    the root and so on for sub-children.
    This is how the Cases are dispatched to the node tree.
    
    This implementation stores everything in several
    dict instances.
    You will need to subclass it and implement some
    persistence/IO in order to be useful.
    (See FileCaseData)
    
    '''
    #TODO: document this class (explain dict sharing stuff and CaseData<=>Case difference)
    #TODO: wtf with this not used argument 'creator'???
    def __init__(self, node_uid, node_type_names, sub_path=(), creator=None):
        '''
        node_uid, node_type_names and sub_path must be tuples (not lists!!!)
        '''
        super(CaseData, self).__init__()
        self.node_uid = node_uid
        self.node_type_names = node_type_names
        self.sub_path = sub_path
        
        self._doc = self.get_mandatory_doc()

    def get_mandatory_doc(self):
        return {'_id':self.node_uid, 'type_names':self.node_type_names}
    
    def get_one_case(self, related_id, type_names):
        related_uid = self.node_uid+self.sub_path+(related_id,)
        ret = self.__class__(related_uid, type_names, creator=self)
        return ret
    
    def get_many_case(self, related_id, type_names):
        related_uid = self.node_uid+self.sub_path+(related_id,)
        ret = self.__class__(related_uid, type_names, creator=self)
        return ret

    def get_child_case(self, related_id, type_names):
        sub_path = self.sub_path+(related_id,)
        ret = self.__class__(self.node_uid, self.node_type_names, sub_path=sub_path, creator=self)
        ret._doc = self._doc # Child case share the same dict
        return ret
    
    def ensure_exists(self):
        pass
    
    def load(self):
        pass
    
    def save(self):
        pass

    def get(self, name, default=None):
        #print '#- GET CASE ITEM:', self.node_uid, self.sub_path, name
        doc = self._doc
        for i in self.sub_path:
            doc = doc.get(i, None)
            if doc is None:
                return default
        return doc.get(name, default)
    
    def __getitem__(self, name):
        return self.get(name)
    
    def set(self, name, value):
        #print '#- SET CASE ITEM:', self.node_uid, self.sub_path, name, value
        doc = self._doc
        for i in self.sub_path:
            sub_doc = doc.get(i, None)
            if sub_doc is None:
                sub_doc = {}
                doc[i] = sub_doc
            doc = sub_doc
        doc[name] = value
        self.save()

    def __setitem__(self, name, value):
        return self.set(name, value)

    def find_cases(self, type_name, under_uid):
        '''
        Returns the uids of all the cases of nodes having the
        given type_name and under the given under_uid.
        '''
        return []
    
class FileCaseData(CaseData):
    '''
    This CaseData subclass stores the data in a file
    under the path found in the '_save_path' attribute.
    If this attribute is None or empty, nothing is read
    nor saved.
    
    NB: This class is old and is not actually used
    by kabaret.studio so it may not be up to date.
    Take it as a starting point if you need to implement
    your very own persistence system.
    
    '''
    
    def __init__(self, node_uid, node_type_names, sub_path=(), creator=None):
        super(FileCaseData, self).__init__(node_uid, node_type_names, sub_path, creator=creator)
        self._save_path = creator and creator._save_path or None

    def _get_path(self):
        # Use types and uid in name as our index system:
        basename = '%s@%s.db'%(
            '.'.join(self.node_type_names),
            '.'.join(self.node_uid).replace(':', '=')
        )
        return os.path.join(self._save_path, basename)
    
    @classmethod
    def _read_file_to_doc(cls, path):
        context = {}
        try:
            execfile(path, context)
        except Exception:
            print '#-- Exception while reading CaseData: '+path
            import traceback
            traceback.print_exc()
            raise
        else:
            try:
                return context['doc']
            except KeyError:
                print '#-- no "doc" in CaseData: '+path
                raise

    @classmethod
    def _get_dotted_key(cls, doc, key, default):
        key_path = key.split('.')
        for i in key_path:
            doc = doc.get(i, None)
            if doc is None:
                return default
        return doc

    @classmethod
    def _has_sub_doc(cls, doc, sub_path):
        v = cls._get_dotted_key(doc, '.'.join(sub_path), None)
        return isinstance(v, dict)
    
    @classmethod
    def _matches(cls, v, got):
        #print '???', k, v, got
        if v is True:
            if not got:
                #print ' :(', got, 'not True'
                return False
        elif v is None:
            #print '??? v is None', k, v, got
            if got is not None:
                #print ' :(', got, 'not None'
                return False
        elif v and isinstance(v, tuple):
            op = v[0]
            v = v[1:]
            #print ' ? OP', op, v 
            if op == '$!':
                if (got == v or got == v[0]):
                    #print ' :( OP:', op, 'got', got, 'on', v
                    return False
            elif op == '$in':
                if got not in v:
                    #print ' :( OP:', op, 'got', got, 'on', v
                    return False
            elif op == '$!in':
                if got in v:
                    #print ' :( OP:', op, 'got', got, 'on', v
                    return False
            elif op == '$has':
                #print ' ? OP $has got:', got, 'on:', v 
                try:
                    if not v[0] in got:
                        #print ' :( v[0] not in got'
                        return False
                except Exception, err:
                    #print ' :( err:', str(err)
                    return False
            elif op == '$!has':
                #print ' ? OP $!has got:', got, 'on:', v 
                try:
                    if v[0] in got:
                        #print ' :( v[0] in got'
                        return False
                except Exception, err:
                    #print ' :( err:', str(err)
                    pass
            elif op == '$>': 
                if not got > v[0]:
                    #print ' :( OP:', op, 'got', got, 'on', v
                    return False
            elif op == '$<':
                if not got < v[0]:
                    #print ' :( OP:', op, 'got', got, 'on', v
                    return False
            elif got != (op,)+v:
                #print ' :(', got, '!=', v
                return False
            #print ' :) OP OK'
        elif got != v:
            #print ' :(', got, '!=', v
            return False
        return True
    
    @classmethod
    def _doc_matches(cls, doc, **where):
        getter = cls._get_dotted_key
        matches = cls._matches
        for k, v in where.items():
            if k == 'node_id':
                # The node_id is stored as the last element of _id
                got = getter(doc, '_id', None)
                # first try on the node_id (last item in uid):
                node_id = got[-1].split(':',1)[-1]
                res = matches(v, node_id)
                if res:
                    # success on node_id is enough
                    continue
                # if node_id did not match, try on the whole uid
            else:
                got = getter(doc, k, None)
            if not matches(v, got):
                return False
        #print ' :)'
        return True
    
    def ensure_exists(self):
        if self._save_path is None:
            print 'Cannot ensure case data exists, path not set.'
            return
        if not os.path.exists(self._get_path()):
            self.save()
            

    def load(self):
        if self._save_path is None:
            print 'Cannot read case data, path not set.'
            return

        path = self._get_path()
        #print '#---- Read CaseData', path

        if not os.path.exists(path):
            self._doc = self.get_mandatory_doc()
            return
        
        self._doc = self._read_file_to_doc(path)
        self._doc.update(self.get_mandatory_doc())
            
    def save(self):
        if self._save_path is None:
            print 'Cannot save case data, path not set.'
            return

        path = self._get_path()
        print '#---- Write CaseData', path
        
        with open(path, 'w') as w:
            w.write('# DB Document: FLOW CaseData\n')
            w.write('\nimport datetime\n\n')
            w.write('doc = '+pprint.pformat(self._doc))
            w.write('\n\n')
                
    def find_cases(self, type_name, under_uid=None, sub_paths=[], **where):
        if self._save_path is None:
            print 'Cannot find cases, path not set.'
            return []
        
        start_time = time.time()
        files = glob.glob1(self._save_path, '*.db')
        joined_under_uid = '.'.join(under_uid).replace(':', '=')
        ret = []
        nb = len(files)
        i = 0
        step = nb / 4
        percent = 0
        print 'Search Begin, %i candidats'%(nb,)
        for file in files:
            i += 1
            if i > step:
                percent += 25
                i = 0
                print str(percent)+'% done'
            #print '======', file
            joined_types, joined_uid = file[:-3].split('@')
            type_names = joined_types.split('.')
            if type_name not in type_names:
                #print '     bad type', type_name, type_names 
                continue
            if under_uid is not None:
                if not joined_uid.startswith(joined_under_uid):
                    #print '     not under', joined_uid, joined_under_uid 
                    continue
            doc = self._read_file_to_doc(os.path.join(self._save_path, file))
            if where and not self._doc_matches(doc, **where):
                #print '    did not match where:', where
                continue
            if sub_paths:
                for sub_path in sub_paths:
                    #TODO: when the case is not yet fully created, we dont find the doc
                    # so for know we dont test the sub doc existence.
                    # -> the full case should be create in relations.many.Many.sync_cases !
                    if 1 or self._has_sub_doc(doc, sub_path):
                        ret.append(doc['_id']+sub_path)
                        #print '     sub match:', doc['_id']+sub_path
            else:
                #print '     match:', doc['_id']
                ret.append(doc['_id'])
        time_taken = time.time()-start_time
        time_str = '%im %is'%(time_taken/60, (time_taken%60)+.5) 
        print 'Search done, %i matchs / %i candidats in %s'%(len(ret), nb, time_str) 
        return ret
