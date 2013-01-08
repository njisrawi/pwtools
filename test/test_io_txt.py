# Test array text input and output

from StringIO import StringIO
from pwtools import arrayio
import os
import numpy as np
from testenv import testdir
pj = os.path.join

def write_read_check(fn, arr, axis=-1, shape=None):
    print fn + ' ...'
    arrayio.writetxt(fn, arr, axis=axis)
    a = arrayio.readtxt(fn, axis=axis, shape=shape)
    assert (a == arr).all()


def test_io_txt():
    # 1d
    a = np.arange(0, 3)
    fn = pj(testdir, 'a1d.txt')
    write_read_check(fn, a)

    # 2d
    shape = (3, 5)
    a = np.arange(0, np.prod(shape)).reshape(shape) 
    fn = pj(testdir, 'a2d.txt')
    write_read_check(fn, a)

    # 3d, store array along axis 0,1,2,-1
    shape = (3, 5, 7)
    a = np.arange(0, np.prod(shape)).reshape(shape)
    
    # ignore file header if shape != None
    for sh in [None, shape]:
        fn = pj(testdir, 'a3d0.txt')
        write_read_check(fn, a, axis=0, shape=sh)
        fn = pj(testdir, 'a3d1.txt')
        write_read_check(fn, a, axis=1, shape=sh)
        fn = pj(testdir, 'a3d2.txt')
        write_read_check(fn, a, axis=2, shape=sh)
        fn = pj(testdir, 'a3dm1.txt')
        write_read_check(fn, a, axis=-1, shape=sh)
    
    # API
    shape = (3, 5)
    arr = np.arange(0, np.prod(shape)).reshape(shape)
    fn = pj(testdir, 'a2d_api.txt')
    fh = open(fn, 'w')
    fh.write('@@ some comment\n')
    fh.write('@@ some comment\n')
    fh.write('@@ some comment\n')
    np.savetxt(fh, arr)
    fh.close()
    a = arrayio.readtxt(fn, shape=shape, axis=-1, comments='@@')
    assert (a == arr).all()

    txt = "1.0 2.0 3\n4   5   6\n"
    arr = arrayio.readtxt(StringIO(txt), shape=(2,3), axis=-1, dtype=float)
    assert arr.dtype == np.array([1.0]).dtype
    # Apparently in Python 2.7: 
    #   float('1.0') -> 1.0
    #   int('1.0')  -> ValueError: invalid literal for int() with base 10: '1.0'
    #   int(float('1.0')) -> 1
    # We need to (ab)use converters. Ugh.  
    arr = arrayio.readtxt(StringIO(txt), shape=(2,3), axis=-1, dtype=int,
                          converters=dict((x,lambda a: int(float(a))) for x in [0,1,2]))
    assert arr.dtype == np.array([1]).dtype
