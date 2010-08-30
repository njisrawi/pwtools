from pwtools import common
from pwtools.sql import SQLEntry, SQLiteDB
fpj = common.fpj

class Machine(object):
    """This is a container for machine specific stuff. Most of the
    machine-specific settings can (and should) be placed in the corresponding
    job template file. But some settings need to be in sync between files (e.g.
    outdir (pw.in) and scratch (job.*). For this stuff, we use this class."""
    def __init__(self, name=None, subcmd=None, scratch=None, bindir=None, 
                 pseudodir=None, jobfn=None):
        # attr_lst
        self.name = name
        self.subcmd = subcmd
        self.scratch = scratch
        self.bindir = bindir
        self.pseudodir = pseudodir
        # extra
        self.jobfn = jobfn

        self.jobtempl = self._get_jobtempl()

        self.attr_lst = ['subcmd', 
                         'scratch',
                         'bindir',
                         'pseudodir',
                         ]

    def get_sql_record(self):
        dct = {}
        for key in self.attr_lst:
            val = getattr(self, attr)
            if val is not None:
                dct[key] = SQLEntry(sql_type='TEXT', sql_val=val)
        return dct
    
    def _get_jobtempl(self):
        return common.FileTemplate(self.jobfn)


def kpointstr(lst, base='nk'):
    """[3,3,3] -> "nk1=3,nk2=3,nk3=3" """
    return ','.join(['%s%i=%i' %(base, i+1, x) for i, x in enumerate(lst)])


def kpointstr_pwin(lst):
    """[3,3,3] -> " 3 3 3 0 0 0" """
    return ' '.join(map(str, lst)) + ' 0 0 0'


adde = Machine(name='adde',
               subcmd='qsub',
               scratch='/local/scratch/schmerler',
               bindir='/home/schmerler/soft/lib/espresso/current/bin',
               pseudodir='/home/schmerler/soft/lib/espresso/pseudo/pseudo_espresso',
               jobfn='job.sge.adde')

mars = Machine(name='mars',
               subcmd='bsub <',
               scratch='/fastfs/schmerle',
               bindir='/home/schmerle/mars/soft/lib/espresso/current/bin',
               pseudodir='/home/schmerle/soft/lib/espresso/pseudo/pseudo_espresso',
               jobfn='job.lsf.mars')

deimos = Machine(name='deimos',
               subcmd='bsub <',
               scratch='/fastfs/schmerle',
               bindir='/home/schmerle/deimos/soft/lib/espresso/current/bin',
               pseudodir='/home/schmerle/soft/lib/espresso/pseudo/pseudo_espresso',
               jobfn='job.lsf.deimos')

local = Machine(name='local',
               subcmd='bash',
               scratch='/tmp',
               bindir='/home/schmerler/soft/lib/espresso/current/bin',
               pseudodir='/home/schmerler/soft/lib/espresso/pseudo/pseudo_espresso',
               jobfn='job.local')

