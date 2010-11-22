#!/usr/bin/env python

"""
This should do the following:

* Start orbited
* Start netserver 
* Start bot
* Optionally start the development web server

"""

#########################################
# Configuration

# Username to run OWGS as
owgs_username = 'sean'

# Path to owgs
owgs_path = '/home/sean/code/go/django_code'

# These are the scripts we will run, and where they will be logged to
executables = [ 

    { 'name': 'devserver',
      'wd': '%s/go' % owgs_path,
      'args': [ '%s/go/manage.py' % owgs_path, 'runserver', '10.200.200.6:8000' ],
      'log': '%s/log/manage.log' % owgs_path },

    { 'name': 'orbited',
      'args': [ '/home/sean/code/go/orbited/start.py', '--config', '/home/sean/code/go/orbited/orbited.cfg' ],
      'log': '%s/log/orbited.log' % owgs_path },
    
    { 'name': 'netserver',
      'args': [ '%s/netserver.py' % owgs_path ],
      'log': '%s/log/netserver.log' % owgs_path },
    
    { 'name': 'gtpbot',
      'args': [ '%s/gtpbot.py' % owgs_path ],
      'log': '%s/log/gtpbot.log' % owgs_path }
    
    
    ]


######################################
# Environment initialization

import os, subprocess, traceback, pwd, sys, time

try:
    owgs_euid = pwd.getpwnam(owgs_username)[2]
    os.seteuid(owgs_euid)
except Exception, e:
    print 'Failed in attempt to seteuid() to %s' % owgs_username
    traceback.print_exc()
    sys.exit()

######################################
# Process launching

procs = []

for ex in executables:
    
    # class subprocess.Popen(args, bufsize=0, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None, close_fds=False, shell=False, cwd=None, env=None, universal_newlines=False, startupinfo=None, creationflags=0)
    
    log = "%s Starting %s: %s" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"), ex['name'], ' '.join(ex['args']))
    print log
    
    try:
        logfile = file(ex['log'], 'a+')        
    except Exception, e:
        print 'Could not open log file %s' % ex['log']
        traceback.print_exc()
        sys.exit()

    # write message indicating when the program was started to the log
    logfile.write(log)
    logfile.flush()

    # prepare cwd argument
    if ex.has_key('wd'):
        setcwd = ex['wd']
    else:
        setcwd = None
    
    proc = subprocess.Popen( args=ex['args'], stdout=logfile, stderr=logfile, cwd=setcwd )
    
    # store it to our procs list
    procs.append( proc )

    
# now we dont die until all processes die
for proc in procs:
    proc.wait()

    
