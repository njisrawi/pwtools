# Test crys.rpdf() against reference results. Test 2 AlN structs from
# examples/rpdf/rpdf_aln.py and one random trajectory with selections (2 atom
# types) and time average.
#
# See examples/rpdf/ for more complete examples.
#
# See utils/gen_rpdf_ref.py for how the references were generated.
#
# Test crys.vmd_measure_gofr(), but only API.

import os
import numpy as np
from pwtools import crys, parse, io
from testenv import testdir
pj = os.path.join

have_vmd = os.system('which vmd > /dev/null 2>&1') == 0

def test():
    for name in ['rand_3d', 'aln_ibrav0_sc', 'aln_ibrav2_sc']:
        print("name: %s" %name)
        dd = 'files/rpdf'
        if name == 'rand_3d':
            cell = np.loadtxt(pj(dd, name + '.cell.txt'))
            coords = [io.readtxt(pj(dd, name + '.coords0.txt')), 
                      io.readtxt(pj(dd, name + '.coords1.txt'))]
            for c in coords:
                assert c.shape == (10,3,20)
        else:
            pp = parse.CifFile(pj(dd, name + '.cif'))
            pp.parse()
            coords = pp.coords
            cell = pp.cell
            symbols = pp.symbols

        # rpdf() 
        rad, hist, num_int = \
            crys.rpdf(coords, 
                      rmax=5.0, 
                      cell=cell,
                      dr=0.05, 
                      pbc=True)
        results = {'rad':       rad,
                   'hist':      hist, 
                   'num_int':   num_int,
                   'rmax_auto': np.array(crys.rmax_smith(cell)),
                   }
        
        # Verification, rpdf() only. See examples/rpdf/compare_vmd/ instead.
        for key, val in results.iteritems():
            print("    key: %s" %key)
            ref = np.loadtxt(pj(dd, "result.%s.%s.txt" %(key, name)))
            np.testing.assert_array_almost_equal(ref, val)
            print("    key: %s ... ok" %key)
        
    if have_vmd:
        rad_vmd, hist_vmd, num_int_vmd = \
            crys.vmd_measure_gofr(coords_frac=np.random.rand(10,3,20), 
                                  cell=np.identity(3)*5,
                                  symbols=['X']*10,
                                  dr=0.05,
                                  selstr1='all',
                                  selstr2='all',
                                  fntype='xsf',
                                  first=0,
                                  last=-1, step=1, usepbc=1, datafn=None,
                                  scriptfn=None, logfn=None, xsffn=None,
                                  tmpdir=testdir,
                                  keepfiles=True,
                                  verbose=False)

