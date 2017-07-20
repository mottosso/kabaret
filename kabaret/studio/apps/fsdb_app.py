'''




'''

import os
import pprint
import glob
import time

from kabaret.core.apps.base import App
from kabaret.core.conf import Config, Group, Attribute, ConfigError

#
#    SETTINGS
#
class FSDBAppSettings(Config):
    '''
    The FSDB App Configuration.

    You can use those variable here:
        project_name:  the name of the project
        store_path:    the store path for the project
        station_class: the name of the staion class (Windows-7, Linux, etc...)
        APP:           the SYSCMD app loading this configuration

    '''
    EXTRA_CONTEXT = {
    }
    
    def _define(self):
        self.ROOT_PATH = Attribute(
            None,
            '''
            The path on the filesystem used to store the data.
            If None, the default will be used (Under the 'TMP'
            dir of the project)
            '''
        )
            
            
#
#    APP
#
class FSDBApp(App):
    APP_KEY = 'DB'
    
    def __init__(self, host):
        super(FSDBApp, self).__init__(host)
        self._root_path = None
        
    def _get_setting_context(self):
        return {
            'project_name' : self.host.project_name,
            'store_path' : self.host.station_config.store_path,
            'station_class' : self.host.station_config.station_class,
            'APP': self,
        }
        
    def _get_setting_class(self):
        return FSDBAppSettings
    
    def _apply_settings(self, settings):
        self._root_path = settings.ROOT_PATH
        if self._root_path is None:
            self._root_path = os.path.join(
                self.host.station_config.project_dirs['TEMP'],
                'FSDB'
            )
            print '#------- FSDB Root not defined, using default: %s'%(self._root_path,)
        else:
            print '#------- FSDB Root set to: %s'%(self._root_path,)
        
        # This used to be done in _host_init_done()
        # but all apps using DB should be able to do so in their 
        # _host_init_done so we must do this here:
        if not os.path.exists(self._root_path):
            dir, name = os.path.split(self._root_path)
            if not os.path.isdir(dir):
                raise ConfigError(
                    'Cannot create %r in %r, folder does not exists.'%(
                        name, dir,
                    )
                )
            print '    Creating FSDB Root:', self._root_path
            os.mkdir(self._root_path)
        
    def get_collection(self, collection_name, index_keys=None):
        return Collection(self._root_path, collection_name, index_keys)

class Collection(object):
    def __init__(self, root_path, name, index_keys=None):
        '''
        Create a manager for the Collection named 'name' under 'root_path'.
        
        The index_keys must be a list of string key names or None.
        It will impact how the collection stores/fetches documents
        and must be consistent with existing documents.
        If None, the default value of ['_id'] is used.
        If '_id' is not specified in index_keys, it will be added.
        
        /!\ The value of the indexed keys in the documents must
        be a string or a tuple of strings (no digit, no list, no dict, 
        no other types).
        Also indexed string value cannot contain the '^' characters, and
        indexed tuple values cannot contain a string with a '=' or a '^'
        character.
        And on windows, the number of characters in the indexed values
        is limited by the file system.
        '''
        
        self._root_path = root_path
        self._name = name
        self._path = os.path.join(self._root_path, self._name)
        self._ensure_exists()
        
        self._index_keys = index_keys or ['_id']
        if '_id' not in self._index_keys:
            self._index_keys.append('_id')
            
    def _ensure_exists(self):
        if not os.path.isdir(self._path):
            if os.path.exists(self._path):
                raise Exception(
                    'Cannot access collection %r: path %r is not a folder.'%(
                        self._name, self._path
                    )
                )
            os.mkdir(self._path)

    def _update_doc(self, to_update, ref):
        '''
        Update the content of the dict 'to_update'
        to match the dict 'ref'.
        
        (The to_update dict is modified)
        '''
        for k in to_update.keys():
            if k not in ref:
                del to_update[k]
        to_update.update(ref)

    def _to_index_infos(self, doc):
        infos = []
        
        for key in self._index_keys:
            v = doc.get(key, None)
            if isinstance(v, tuple):
                for i in v:
                    for c in '.=':
                        if c in i:
                            raise ValueError(
                                'The character %r is not allowed in indexed tuple value (found %r)'%(
                                    c, v
                                )
                            )
                v = '.'.join(v)
            elif not isinstance(v, basestring):
                raise ValueError(
                    'The value of indexed key must be a str or a tuple of str, not %r (%s) (doc: %r)'%(
                        v, type(v), doc
                    )
                )
            else:
                if '=' in v:
                    raise ValueError(
                        'The character %r is not allowed in indexed string value (found %r)'%(
                            '^', v
                        )
                    )
            v = v.replace(':', '=')
            infos.append(v)

        return infos
    
    def _from_index_infos(self, infos):
        doc = {}
        infos = list(infos)
        for key in self._index_keys:
            try:
                info = infos.pop(0)
            except IndexError:
                break
            
            info = info.replace('=', ':')
            if '.' in info:
                info = info.split('.')
            doc[key] = info
        return doc 
    
    def _get_doc_name(self, doc):
        '''
        Returns the name of the document.
        The name depends on the index_keys set in 
        the Collection constructor and the value those
        keys have in the given document.
        '''
            
        name = ('@'.join(self._to_index_infos(doc)))+'.db'
        return name

    def _get_doc_path(self, doc, name=None):
        '''
        Returns the path of the file
        storing the given document.
        
        If name is not None, it will override the
        value deduced from the content of the doc.
        '''
        return os.path.join(self._path, name and name or self._get_doc_name(doc))
    
    def get_doc(self, mandatory_doc={}):
        '''
        Reads and returns a complete doc as a dict.
        
        The mandatory_doc is a doc used to identify the 
        document: its should contain the keys set as 
        the Collection index_keys.
        
        The returned doc will be conformed to the
        mandatory_doc: it will contains at least its keys and
        values.
        
        The mandatory_doc is returned if the document it
        is pointing does not exists in the Collection.
        '''
        doc_path = self._get_doc_path(mandatory_doc)
        if not os.path.exists(doc_path):
            return mandatory_doc
        
        doc = self._read_file_to_doc(doc_path)
        doc.update(mandatory_doc)
        
        return doc

    def _read_file_to_doc(self, path):
        context = {}
        try:
            execfile(path, context)
        except Exception:
            print '#-- Exception while reading document in FSDB Collection: '+path
            import traceback
            traceback.print_exc()
            raise
        else:
            try:
                return context['doc']
            except KeyError:
                print '#-- no "doc" in FSDB Collection\'s document file: '+path
                raise

    def get(self, doc, key, default=None):
        '''
        Returns the value of the key in the document.

        The key may contain '.' and lead to a sub-document
        key.

        /!\ If the key is not found, the document is reloaded
        and a second attempt is made.
        The updated value (or default) is returned, and 
        the given 'doc' is updated!
        '''
        succeed, result = self._get(doc, key, default)
        if succeed:
            return result
        
        # Not found, let's check on disk
        doc_path = self._get_doc_path(doc)
        if not os.path.exists(doc_path):
            return default
        fresh_doc = self._read_file_to_doc(doc_path)
        self._update_doc(doc, fresh_doc)
        
        # retry
        succeed, result = self._get(fresh_doc, key, default)
        if succeed:
            return result    
        
        # Still not succeeded, we set the
        # default and return it:
        self.set(doc, key, default)
        return default
        

    @classmethod
    def _get(cls, doc, key, default):
        if '.' in key:
            sub_keys = key.split('.')
            key = sub_keys.pop()
            for i in sub_keys:
                try:
                    doc = doc[i]
                except KeyError:
                    return False, None
        try:
            return True, doc[key]
        except KeyError:
            return False, default
        
    def set_doc(self, doc):
        '''
        Store a complete document.
        '''
        doc_path = self._get_doc_path(doc)
        self._write_doc_to_file(doc_path, doc)
        
    def _write_doc_to_file(self, path, doc):
        print '===========> WRITE DOC', path
        with open(path, 'w') as w:
            w.write('# DB Document:\n')
            w.write('\nimport datetime\n\n')
            w.write('doc = '+pprint.pformat(doc))
            w.write('\n\n')

    def set(self, doc, key, value):
        '''
        Sets the key to value in the given document
        (and store it on disk)
        
        The key may contain '.' and lead to a sub-document
        key.
        
        If the value is None and the key exists, it
        is deleted from the document.
        '''
        # Read the doc to update other values:
        doc_path = self._get_doc_path(doc)
        if os.path.exists(doc_path):
            fresh_doc = self._read_file_to_doc(doc_path)
            self._update_doc(doc, fresh_doc)
        
        # Set this key:
        write_doc = doc
        if '.' in key:
            sub_keys = key.split('.')
            key = sub_keys.pop()
            for i in sub_keys:
                try:
                    sub_doc = write_doc[i]
                except KeyError:
                    sub_doc = {}
                    write_doc[i] = sub_doc
                write_doc = sub_doc
        
        if value is None:
            if key in write_doc:
                del write_doc[key]
            else:
                return
        else:
            write_doc[key] = value
        
        # Save the resulting document:
        self.set_doc(doc)

    def find(self, sub_paths=[], **where):
        '''
        Returns the _id field (or each field in sub_paths) for every
        document matching the 
        '''
        start_time = time.time()
        
        indexed_where = {}
        for k in where.keys():
            if k in self._index_keys:
                indexed_where[k] = where.pop(k)
                                
        files = glob.glob1(self._path, '*.db')
        ret = []
        nb = len(files)
        i = 0
        step = nb / 4
        percent = 0
        print 'Search Begin, %i candidats'%(nb,)
        for basename in files:
            #print '======', basename
            i += 1
            if i > step:
                percent += 25
                i = 0
                print str(percent)+'% done'

            # Start by matching indexed infos, they are
            # available w/o reading the file                
            indexed_infos = basename[:-3].split('@')
            doc = self._from_index_infos(indexed_infos)
            
            #print 'TESTING INDEXES', doc, indexed_where
            if indexed_where and not self._doc_matches(doc, **indexed_where):
                #print ' NOPE'
                continue
            
            # Indexed infos match, let's match the content of the file:
            doc = self._read_file_to_doc(self._get_doc_path(doc, basename))
            #print 'TESTING WHERE:', pprint.pprint(where)
            #print 'ON DOCUMENT:', pprint.pprint(doc)
            if where and not self._doc_matches(doc, **where):
                #print '    did not match where:', where
                continue
            
            if sub_paths:
                for sub_path in sub_paths:
                    #TODO: should we skip when the sub_path does not exists?
                    ret.append(doc['_id']+sub_path)
                    #print '     sub match:', doc['_id']+sub_path
            else:
                #print '     match:', doc['_id']
                ret.append(doc['_id'])
                
        time_taken = time.time()-start_time
        time_str = '%im %is'%(time_taken/60, (time_taken%60)+.5) 
        print 'Search done, %i matchs / %i candidats in %s'%(len(ret), nb, time_str) 
        return ret
        
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
            elif op == '$under':
                if got != v[0]:
                    try:
                        gs = '/'.join([ repr(i) for i in got ])
                        vs = '/'.join([ repr(i) for i in v[0] ])+'/'
                        if not gs.startswith(vs):
                            #print ' :( OP:', op, 'got', got, 'on', v
                            return False
                    except Exception, err:
                        #print ' :( OP:', op, 'got', got, 'on', v, 'ERROR:', err
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
        getter = cls._get
        matches = cls._matches
        for k, v in where.items():
            if k == 'node_id': #TODO: this is FLOW related and should not be here!!!
                # The node_id is stored as the last element of _id
                succeed, got = getter(doc, '_id', None)
                if not succeed and v is not None:
                    return False
                # first try on the node_id (last item in uid):
                node_id = got[-1].split(':',1)[-1]
                res = matches(v, node_id)
                if res:
                    # success on node_id is enough
                    continue
                # if node_id did not match, try on the whole uid
            else:
                succeed, got = getter(doc, k, None)
                if not succeed and v is not None:
                    return False
            #print '????', v, k, succeed, got
            if not matches(v, got):
                return False
        #print ' :)'
        return True


