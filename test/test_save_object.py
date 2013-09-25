# Data persistence. Parse some data into a PwMDOutputFile object and save the
# whole object in binary to disk using the dump() method, which actually uses
# cPickle. 

import os, tempfile
import numpy as np
from pwtools.parse import PwMDOutputFile
from pwtools import common, crys, io
from testenv import testdir
from pwtools.test.tools import ade

rand = np.random.rand

def test_save_object():
    tmpdir = tempfile.mkdtemp(dir=testdir, prefix=__file__)
    base = 'pw.md.out'
    filename = '{tdr}/{base}'.format(tdr=tmpdir, base=base)
    cmd = "mkdir -p {tdr}; cp files/{base}.gz {tdr}/; \
           gunzip {fn}.gz;".format(tdr=tmpdir,
                                   base=base, fn=filename)
    common.system(cmd, wait=True)
    assert os.path.exists(filename)
    dumpfile = os.path.join(testdir, 'pw.md.pk')

    c = PwMDOutputFile(filename=filename)
    print ">>> parsing ..."
    c.parse()
    print ">>> ... done"

    print ">>> saving %s ..." %dumpfile
    c.dump(dumpfile)
    print ">>> ... done"

    print ">>> loading ..."
    c2 = PwMDOutputFile()
    c2.load(dumpfile)
    print ">>> ... done"

    print ">>> checking equalness of attrs in loaded object ..."
    known_fails = {'fd': 'closed/uninitialized file',
                   'cont': 'container object'}
    arr_t = type(np.array([1]))
    dict_t = type({})
    for attr in c.__dict__.iterkeys():
        c_val = getattr(c, attr)
        c2_val = getattr(c2, attr)
        dotest = True
        for name, string in known_fails.iteritems():
            if name == attr:
                print "%s: KNOWNFAIL: %s: %s" %(name, string, attr)
                dotest = False
        if dotest:
            print "testing:", attr, type(c_val), type(c2_val)
            type_c = type(c_val)
            type_c2 = type(c2_val)
            assert type_c is type_c2, "attr: %s: types differ: %s, %s" \
                %(attr, str(type_c), str(type_c2))
            if type(c_val) is arr_t:
                assert (c_val == c2_val).all(), "fail: %s: %s, %s" \
                                                %(attr, c_val, c2_val)
            elif type(c_val) is dict_t:
                ade(c_val, c2_val)
            else:
                assert c_val == c2_val, "fail: %s: %s, %s" \
                                        %(attr, c_val, c2_val)

def test_save_mkdir():
    path = os.path.join(testdir, 'foo', 'bar', 'baz')
    assert not os.path.exists(path)
    fn = os.path.join(path, 'grr.pk')
    st = crys.Structure(coords=rand(10,3), cell=rand(3,3), symbols=['H']*10)
    st.dump(fn, mkdir=True)
    io.cpickle_load(fn)
