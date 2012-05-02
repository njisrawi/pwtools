import os
import shutil
import warnings
import numpy as np
from pwtools import common
from pwtools.sql import SQLEntry, SQLiteDB
from pwtools.verbose import verbose
pj = os.path.join

# backwd compat
from pwtools.sql import sql_column, sql_matrix

class Machine(object):
    """This is a container for machine-specific stuff. Most of the
    machine-specific settings can (and should) be placed in the corresponding
    job template file. But some settings need to be in sync between files (e.g.
    outdir (pw.in) and scratch (job.*). For this stuff, we use this class.
    
    Useful to predefine commonly used machines.

    Note that the template file for the jobfile is not handled by this class.
    This must be done outside by FileTemplate. We only provide a method to
    store the jobfile name (`jobfn`).

    methods:
    --------
    get_sql_record() : Return a dict of SQLEntry instances. Each key is a
        attr name from self.attr_lst.        
    """
    def __init__(self, hostname=None, subcmd=None, scratch=None, 
                 jobfn=None, home=None, name=None):
        """
        args:
        -----
        hostname : st
            machine name ('mars', 'local', ...)
        subcmd : str
            shell command to submit jobfiles (e.g. 'bsub <', 'qsub')
        scratch : str
            scratch dir
        jobfn : str
            basename of jobfile, can be used as FileTemplate(basename=jobfn)
        home : str
            $HOME
        """
        if name is not None:
            warnings.simplefilter('always')
            warnings.warn("`name` is deprecated, use `hostname` instead , "
                "self.hostname = name will used, self.name will be set but "
                "not appear in the output of self.get_sql_record()", 
                DeprecationWarning)
            hostname = name
            self.name = hostname
        # attr_lst
        self.hostname = hostname
        self.subcmd = subcmd
        self.scratch = scratch
        self.home = home
        # extra
        if os.sep in jobfn:
            raise StandardError("Path separator in `jobfn`: '%s', "
                  "this should be a basename." %jobfn)
        self.jobfn = jobfn
                
        self.attr_lst = ['hostname',
                         'subcmd', 
                         'scratch',
                         'jobfn',
                         'home'
                         ]

    def get_sql_record(self):
        dct = {}
        for key in self.attr_lst:
            val = getattr(self, key)
            if val is not None:
                dct[key] = SQLEntry(sqltype='TEXT', sqlval=val)
        return dct
    
    def get_queue(self, ncores):
        """Return string with batch queue name based on requested number of
        cores `ncores`.

        args:
        -----
        ncores : int
        """
        return None


class FileTemplate(object):
    """Class to represent a template file in parameter studies.
    
    placeholders
    ------------
    Each template file is supposed to contain a number of placeholder strings
    (e.g. XXXFOO or @foo@ or whatever other form). The `dct` passed to
    self.write() is a dict which contains key-value pairs for replacement (e.g.
    {'foo': 1.0, 'bar': 'say-what'}, keys=dct.keys()). Each key is converted to
    a placeholder by `func`.
    
    We use common.template_replace(..., mode='txt'). dict-style placeholders
    like "%(foo)s %(bar)i" will not work.

    example
    -------
    This will take a template file calc.templ/pw.in, replace the placeholders
    "@prefix@" and "@ecutwfc@" with some values and write the file to
    calc/0/pw.in .
    
    # Fist, set up a dictionary which maps placeholder to values. Remember,
    # that the placeholders in the files will be obtained by processing the
    # dictionary keys with `func`. In the example, this will be
    #   'prefix' -> '@prefix@'
    #   'ecutwfc' -> '@ecutwfc@'
    >>> dct = {}
    >>> dct['prefix'] = 'foo_run_1'
    >>> dct['ecutwfc'] = 23.0
    >>>
    # Not specifying the `keys` agrument to FileTemplate will instruct the
    # write() method to replace all placeholders in the template file which
    # match the placeholders defined by dct.keys(). This is the most simple
    # case.
    #
    >>> templ = FileTemplate(basename='pw.in',
    ...                      templ_dir='calc.templ', 
    ...                      func=lambda x: "@%s@" %x)
    >>> templ.write(dct, 'calc/0')
    >>> 
    # Now with `keys` explicitely.
    #
    >>> templ = FileTemplate(basename='pw.in',
    ...                      keys=['prefix', 'ecutwfc'],
    ...                      templ_dir='calc.templ',
    ...                      func=lambda x: "@%s@" %x)
    >>> templ.write(dct, 'calc/0')
    >>>
    #
    # or with SQL foo in a parameter study
    #
    >>> from sql import SQLEntry
    >>> dct = {}                     
    >>> dct['prefix']  = SQLEntry(sqlval='foo_run_1')
    >>> sct['ecutwfc'] = SQLEntry(sqlval=23.0)
    >>> templ.writesql(dct, 'calc/0')
    """
    def __init__(self, basename='pw.in', keys=None, templ_dir='calc.templ',
                 func=lambda x:'XXX'+x.upper()):
        """
        args
        ----
        basename : string
            The name of the template file and target file.
            example: basename = pw.in
                template = calc.templ/pw.in
                target   = calc/0/pw.in
        keys : {None, list of strings, []}
            keys=None: All keys dct.keys() in self.write() are used. This is
                useful if you have a dict holding many keys, whose placeholders
                are spread across files. Then this will just replace every
                match in each file. This is what most people want.
            keys=[<key1>, <key2>, ...] : Each string is a key. Each key is
                connected to a placeholder in the template. See func. This is
                for binding keys to template files, i.e. replace only these
                keys.
            keys=[]: The template file is simply copied to `calc_dir` (see
                self.write()).
        templ_dir : dir where the template lives (e.g. calc.templ)
        func : callable
            A function which takes a string (key) and returns a string, which
            is the placeholder corresponding to that key.
            example: (this is actually default)
                key = "lala"
                placeholder = "XXXLALA"
                func = lambda x: "XXX" + x.upper()
        """
        self.keys = keys
        self.templ_dir = templ_dir
        
        # We hardcode the convention that template and target files live in
        # different dirs and have the same name ("basename") there.
        #   template = <dir>/<basename>
        #   target   = <calc_dir>/<basename>
        # e.g.
        #   template = calc.templ/pw.in
        #   target   = calc/0/pw.in
        # Something like
        #   template = ./pw.in.templ
        #   target   = ./pw.in
        # is not possible.
        self.basename = basename
        self.filename = pj(self.templ_dir, self.basename)
        self.func = func
        
        self._get_placeholder = self.func
        
    def write(self, dct, calc_dir='calc', mode='dct'):
        """Write file self.filename (e.g. calc/0/pw.in) by replacing 
        placeholders in the template (e.g. calc.templ/pw.in).
        
        args:
        -----
        dct : dict 
            key-value pairs, dct.keys() are converted to placeholders with
            self.func()
        calc_dir : str
            the dir where to write the target file to
        mode : str, {'dct', 'sql'}
            mode='dct': replacement values are dct[<key>]
            mode='sql': replacement values are dct[<key>].fileval and every
                dct[<key>] is an SQLEntry instance
        """
        assert mode in ['dct', 'sql'], ("Wrong 'mode' kwarg, use 'dct' "
                                        "or 'sql'")
        # copy_only : bypass reading the file and passing the text thru the
        # replacement machinery and getting the text back, unchanged. While
        # this works, it is slower and useless.
        if self.keys == []:
            _keys = None
            txt = None
            copy_only = True
        else:
            if self.keys is None:
                _keys = dct.iterkeys()
                warn_not_found = False
            else:
                _keys = self.keys
                warn_not_found = True
            txt = common.file_read(self.filename)
            copy_only = False
        
        tgt = pj(calc_dir, self.basename)
        verbose("write: %s" %tgt)
        if copy_only:    
            verbose("write: ignoring input, just copying file: %s -> %s"
                    %(self.filename, tgt))
            shutil.copy(self.filename, tgt)
        else:            
            rules = {}
            for key in _keys:
                if mode == 'dct':
                    rules[self._get_placeholder(key)] = dct[key]
                elif mode == 'sql':                    
                    # dct = sql_record, a list of SQLEntry's
                    rules[self._get_placeholder(key)] = dct[key].fileval
                else:
                    raise StandardError("'mode' must be wrong")
            new_txt = common.template_replace(txt, 
                                              rules, 
                                              mode='txt',
                                              conv=True,
                                              warn_not_found=warn_not_found)
            common.file_write(tgt, new_txt) 
                                  
    def writesql(self, sql_record, calc_dir='calc'):
        self.write(sql_record, calc_dir=calc_dir, mode='sql')


class Calculation(object):
    """A single calculation, e.g. in dir calc_foo/0/ .
    
    methods:
    --------
    get_sql_record : Return a dict of SQLEntry instances. Each key is a
        candidate placeholder for the FileTemplates.
    write_input : For each template in `templates`, write an input file to
        `calc_dir`.

    notes:
    ------
    The dir where file templates live is defined in the FileTemplates (usually
    'calc.templ').
    
    Default keys in sql_record:
        idx : self.idx
        prefix : self.prefix
        calc_dir : self.calc_dir
            Usually the relative path of the calculation dir.
        calc_dir_abs : absolute path
    """
    # XXX ATM, the `params` argument is a list of SQLEntry instances which is
    # converted to a dict self.sql_record. This is fine in the context of
    # ParameterStudy (esp. with helper functions like sql.sql_column()) and
    # also necessary b/c ParameterStudy must know about sqlite types. (The fact
    # that it is a list rather then a dict in the first place is that the
    # parameter set usually comes from comb.nested_loops(), which returns
    # lists.)
    #
    # But this may be overly complicated if this class is used alone, where a
    # single Calculation will not write a sqlite database, just deal with
    # `templates`. Then a simple dict (without SQLEntry instances) to pass in
    # the params might do it. Keep in mind that in this situation, Calculation
    # should have no kowledge of sql at all. This is kept strictly in
    # ParameterStudy. Maybe allow `params` to be either a dict or a list of
    # SQLEntry instances. In the dict case, let get_sql_record() raise a
    # warning.
    def __init__(self, machine, templates, params, prefix='calc',
                 idx=0, calc_dir='calc_dir'):
        """
        args:
        -----
        machine : instance of batch.Machine
            The get_sql_record() method is used to add machine-specific
            parameters to the FileTemplates.
        templates : dict or list
            Dict or list of FileTemplate instances. Dict is here for backward
            compat, but the keys are actually not used at all.
        params : sequence of SQLEntry instances
            A single "parameter set". The `key` attribute (=sql column name) of
            each SQLEntry will be converted to a placeholder in each
            FileTemplate and an attempt to replacement in the template files is
            made.
        prefix : str, optional
            Unique string identifying this calculation. Usually the base of a
            string for the jobname in a batch queue script. See also ``prefix``
            in ParameterStudy.
        idx : int, optional
            The number of this calculation. Useful in ParameterStudy.
        calc_dir : str, optional
            Calculation directory to which input files are written.
        """
        self.machine = machine
        if type(templates) == type([]):
            self.templates = dict([(ii, val) for ii,val in \
                                   enumerate(templates)])
        else:
            self.templates = templates
        self.params = params
        self.prefix = prefix
        self.idx = idx
        self.calc_dir = calc_dir
        
        self.sql_record = {}
        self.sql_record['idx'] = SQLEntry(sqltype='integer', sqlval=self.idx)
        self.sql_record['prefix'] = SQLEntry(sqltype='text',sqlval=self.prefix)
        self.sql_record['calc_dir'] = SQLEntry(sqltype='text',
                                               sqlval=self.calc_dir)
        self.sql_record['calc_dir_abs'] = SQLEntry(sqltype='text',
                                                   sqlval=common.fullpath(self.calc_dir))
        self.sql_record.update(self.machine.get_sql_record())
        for entry in self.params:
            self.sql_record[entry.key] = entry
    
    def get_sql_record(self):
        return self.sql_record

    def write_input(self):
        if not os.path.exists(self.calc_dir):
            os.makedirs(self.calc_dir)
        for templ in self.templates.itervalues():
            templ.writesql(self.sql_record, self.calc_dir)


class ParameterStudy(object):
    """Class to represent a parameter study, i.e. a number of Calculations,
    based on template files.
    
    methods:
    --------
    write_input : Create calculation dir(s) for each parameter set and write
        input files based on ``templates``. Write sqlite database storing all
        relevant parameters. Write (bash) shell script to start all
        calculations (run locally or submitt batch job file, depending on
        machine.subcmd).
    
    notes:
    ------
    The basic idea is to assemble all to-be-varied parameters in a script
    outside (`params_lst`) and pass these to this class along with a list
    of input and job file `templates`. Then, a simple loop over the parameter
    sets is done and input files are written. 
    
    Calculation dirs are numbered automatically. The default is
        calc_dir = <calc_root>/<calc_dir_prefix>_<machine.hostname>, e.g.
        ./calc_foo
    and each calculation for each parameter set
        ./calc_foo/0
        ./calc_foo/1
        ./calc_foo/2
        ...
    
    A sqlite database calc_dir/<db_name> is written. If this class operates
    on a calc_dir where such a database already exists, then the default is
    to append new calculations. The numbering of calc dirs continues at the
    end. This can be changed with the ``mode`` kwarg of write_input().
    
    Rationale:
    B/c the pattern in which (any number of) parameters will be varied may be
    arbitrary complex, it is up to the user to prepare the parameter sets. Each
    calculation (each parameter set) gets its own dir. Calculations should be
    simply numbered. No fancy naming conventions. Parameters (and results) can
    then be extracted using SQL in any number of ways. Especially wenn adding
    calculations later to an already performed study, we just extend the sqlite
    database.
    
    example:
    --------
    The `params_lst` list of lists is a "matrix" which in fact represents the
    sqlite database table. 
    
    The most simple case is when we vary only one parameter (e.g. the
    cutoff):
        [[SQLEntry(key='foo', sqlval=1.0)], 
         [SQLEntry(key='foo', sqlval=2.0)]]
    The sqlite database would have one column and look like this:
        foo   
        ---   
        1.0   # calc_foo/0
        2.0   # calc_foo/1
    Note that you have one entry per row [[...], [...]], like in a
    column vector, b/c "foo" is a *column* in the database and b/c each
    calculation is represented by one row (record).
    
    Another example is a 2x2 setup (vary 2 parameters 'foo' and 'bar').
      [[SQLEntry(key='foo', sqlval=1.0), SQLEntry(key='bar', sqlval='lala')],
       [SQLEntry(key='foo', sqlval=2.0), SQLEntry(key='bar', sqlval='huhu')]]
    Here we have 2 parameters "foo" and "bar" and the sqlite db would
    thus have two columns.              
        foo   bar
        ---   ---
        1.0   lala  # calc_foo/0
        2.0   huhu  # calc_foo/1
    Each row (or record in sqlite) will be one Calculation, getting
    it's own dir.

    More complex examples:

    Vary two (three, ...) params on a 2d (3d, ...) grid: In fact, the
    way you are constructing params_lst is only a matter of zip() and
    comb.nested_loops().
    
    >>> par1 = sql.sql_column('par1', [1,2,3])
    >>> par2 = sql.sql_column('par2', ['a','b'])
    >>> par3 = ...
    
    # 2d grid
    >>> params_lst = comb.nested_loops([par1, par2])
    # or
    >>> params_lst = []
    >>> for par1 in [1,2,3]:
    ...     for par2 in ['a','b']:
    ...         params_lst.append([sql.SQLEntry(key='par1', sqlval=par1),
    ...                            sql.SQLEntry(key='par2', sqlval=par2),
    ...                            ])
    
    # 3d grid   
    >>> params_lst = comb.nested_loops([par1, par2, par3])
    # or
    >>> params_lst = []
    >>> for par1 in [1,2,3]:
    ...     for par2 in ['a','b']:
    ...         for par3 in [...]:
    ...             params_lst.append([sql.SQLEntry(key='par1', sqlval=par1),
    ...                                sql.SQLEntry(key='par2', sqlval=par2),
    ...                                sql.SQLEntry(key='par3', sqlval=par3),
    ...                                ])
    
    # vary par1 and par2 together, and par3 -> 2d grid w/ par1+par2 on one
    axis and par3 on the other
    >>> params_lst = comb.nested_loops([zip(par1, par2), par3], flatten=True)
    
    That's all.
    
    An alternative way of doing the 2d grid is using sql_matrix:
    >>> pars = comb.nested_loops([[1,2,3], ['a', 'b']])
    >>> params_lst = sql.sql_matrix(pars, [('par1', 'integer'), 
    >>>                                    ('par2', 'text')])

    Even more complex:
    See test/test_parameter_study.py, esp. the test "Incomplete parameter
    sets".

    see also:
    ---------
    comb.nested_loops
    sql.sql_column
    sql.sql_matrix
    """
    def __init__(self, machine, templates, params_lst, prefix='calc',
                 db_name='calc.db', db_table='calc', calc_dir=None, calc_root=os.curdir,
                 calc_dir_prefix='calc'):
        """                 
        args:
        -----
        machine, templates : see Calculation
        params_lst : list of lists
            The "parameter sets". Each sublist is a set of calculation
            parameters as SQLEntry instances: 
                [[SQLEntry(...), SQLEntry(...), ...], # calc_foo/0
                 [SQLEntry(...), SQLEntry(...), ...], # calc_foo/1
                 ...
                ] 
            For each sublist, a separate calculation dir is created and
            populated with files based on `templates`. The `key` attribute of
            each SQLEntry will be converted to a placeholder in each
            FileTemplate and an attempt to replacement in the template files is
            made. Thus, the way placeholders are created is defined in
            FileTemplate, not here!
            Note: Each sublist (parameter set) is flattened, so that it
            can in fact be a nested list, e.g. params_lst = the result of a
            complex comb.nested_loops() call. Also, sublists need not have the
            same length or `key` attributes per entry ("incomplete parameter
            sets"). The sqlite table header is compiled from all distinct
            `key`s found.
        prefix : str, optional
            Calculation name. From this, the prefix for input files and job
            name etc. will be built. By default, a string "_run<idx>" is
            appended to create a unique name.
        db_name : str, optional
            Basename of the sqlite database.
        db_table : str, optional
            Name of the sqlite database table.
        calc_dir : str, optional
            Top calculation dir (e.g. 'calc_foo' and each calc in
            'calc_foo/0, ...').
            If None then default is <calc_root>/<calc_dir_prefix>_<machine.hostname>/
        calc_root : str, optional
            Root of all dirs.
        calc_dir_prefix : str, optional
            Prefix for the top calculation dir (e.g. 'calc' for 'calc_foo').
        """            
        self.machine = machine
        self.templates = templates
        self.params_lst = params_lst
        self.prefix = prefix
        self.db_name = db_name
        self.db_table = db_table
        self.calc_root = calc_root
        self.calc_dir_prefix = calc_dir_prefix
        if calc_dir is None:
            self.calc_dir = pj(self.calc_root, self.calc_dir_prefix + \
                               '_%s' %self.machine.hostname)
        else:
            self.calc_dir = calc_dir
        self.dbfn = pj(self.calc_dir, self.db_name)

    def write_input(self, mode='a', backup=True, sleep=0):
        """
        args:
        -----
        mode : str, optional
            Fine tune how to write input files (based on ``templates``) to calc
            dirs calc_foo/0/, calc_foo/1/, ... . Note that this doesn't change
            the base dir calc_foo at all, only the subdirs for each calc.
            {'a', 'w'}
            'a': Append mode (default). If a previous database is found, then
                subsequent calculations are numbered based on the last 'idx'.
                calc_foo/0 # old
                calc_foo/1 # old
                calc_foo/2 # new
                calc_foo/3 # new
            'w': Write mode. The target dirs are purged and overwritten. Also,
                the database (self.dbfn) is overwritten. Use this to
                iteratively tune your inputs, NOT for working on already
                present results!
                calc_foo/0 # new
                calc_foo/1 # new
        backup : bool, optional
            Before writing anything, do a backup of self.calc_dir if it already
            exists.
        sleep : int, optional
            For the script to start (submitt) all jobs: time in seconds for the
            shell sleep(1) commmand.
        """
        assert mode in ['a', 'w'], "Unknown mode: '%s'" %mode
        if os.path.exists(self.calc_dir):
            if backup:
                common.backup(self.calc_dir)
            if mode == 'w':
                os.remove(self.dbfn)
        else:        
            os.makedirs(self.calc_dir)
        have_new_db = not os.path.exists(self.dbfn)
        # this call creates a file ``self.dbfn`` if it doesn't exist
        sqldb = SQLiteDB(self.dbfn, table=self.db_table)
        # max_idx: counter for calc dir numbering
        if have_new_db:
            max_idx = -1
        else:
            if mode == 'a':
                if sqldb.has_column('idx'):
                    max_idx = sqldb.execute("select max(idx) from %s" \
                    %self.db_table).fetchone()[0]
                else:
                    raise StandardError("database '%s': table '%s' has no "
                          "column 'idx', don't know how to number calcs"
                          %(self.dbfn, self.db_table))
            elif mode == 'w':
                max_idx = -1
        run_txt = "here=$(pwd)\n"
        sql_records = []
        for _idx, params in enumerate(self.params_lst):
            params = common.flatten(params)
            idx = max_idx + _idx + 1
            calc_subdir = pj(self.calc_dir, str(idx))
            calc = Calculation(machine=self.machine,
                               templates=self.templates,
                               params=params,
                               prefix=self.prefix + "_run%i" %idx,
                               idx=idx,
                               calc_dir=calc_subdir)
            if mode == 'w' and os.path.exists(calc_subdir):
                shutil.rmtree(calc_subdir)
            calc.write_input()                               
            sql_records.append(calc.get_sql_record())
            run_txt += "cd %i && %s %s && cd $here && sleep %i\n" %(idx,\
                        self.machine.subcmd, self.machine.jobfn, sleep)
        common.file_write(pj(self.calc_dir, 'run.sh'), run_txt)
        # for incomplete parameters: collect header parts from all records and
        # make a set = unique entries
        raw_header = [(key, entry.sqltype.upper()) for record in sql_records \
            for key, entry in record.iteritems()]
        header = list(set(raw_header))
        if have_new_db:
            sqldb.create_table(header)
        else:
            for record in sql_records:
                for key, entry in record.iteritems():
                    if not sqldb.has_column(key):
                        sqldb.add_column(key, entry.sqltype.upper())
        for record in sql_records:
            cmd = "insert into %s (%s) values (%s)"\
                %(self.db_table,
                  ",".join(record.keys()),
                  ",".join(['?']*len(record.keys())))
            sqldb.execute(cmd, tuple(entry.sqlval for entry in record.itervalues()))
        sqldb.finish()


def conv_table(xx, yy, ffmt="%15.4f", sfmt="%15s"):
    """Convergence table. Assume that quantity `xx` was varied, resulting in
    `yy` values. Return a string (table) listing 
        x, y, diff-next, diff-last 
    where each row of diff-next is np.diff(y), i.e. the difference to the *next*
    row and diff-last the difference to the lase value yy[-1].
    
    Useful for quickly viewing the results of a convergence study, where we
    assume that the sequence yy[0], yy[1], ... yy[-1] converges to some
    constant value.

    args:
    -----
    xx : 1d sequence (need not be numpy array)
    yy : 1d sequence, len(xx), must be convertable to numpy float array
    ffmt, sfmt : str
        Format strings for strings and floats
    
    example:
    --------
    >>> kpoints = ['2 2 2', '4 4 4', '8 8 8']
    >>> etot = [-300.0, -310.0, -312.0]
    >>> print conv_table(kpoints, etot)
              x              y      diff-next      diff-last
          2 2 2      -300.0000       -10.0000        12.0000
          4 4 4      -310.0000        -2.0000         2.0000
          8 8 8      -312.0000         0.0000         0.0000
    """
    yy = np.asarray(yy, dtype=np.float)
    lenxx = len(xx)
    dyy = yy[:,None].repeat(2,1)
    # dyy: column 0: diff-next
    # dyy: column 1: diff-last
    dyy[-1,0] = 0.0
    dyy[:-1,0] = np.diff(yy)
    dyy[:,1] = yy[-1] - dyy[:,1]
    st = (sfmt*4 + "\n") %("x", "y", "diff-next", "diff-last")
    fmtstr = ("%s"*4 + "\n") %((sfmt,) + (ffmt,)*3)
    for idx in range(lenxx):
        st += fmtstr %(xx[idx], yy[idx], dyy[idx,0], dyy[idx,1])
    return st
