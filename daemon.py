#!/usr/bin/env python

"""
This should do the following:

* Start orbited
* Start netserver 
* Start bot
* Optionally start the development web server

"""

######################################
# Environment initialization

import os, subprocess, traceback, pwd, sys, time, ConfigParser

config = ConfigParser.ConfigParser()
config.read('daemon.cfg')
def parseCfg(name):
    return config.get('owgs', name)

# Username to run OWGS as
owgs_username = parseCfg('user')

# These are the scripts we will run, and where they will be logged to
executables = [ 

    { 'name': 'devserver',
      'disabled': (parseCfg('django_manage') == 'N'),
      'cmd': parseCfg('django_command'),
      'log': parseCfg('django_log') },

    { 'name': 'orbited',
      'cmd': parseCfg('orbited_command'),
      'log': parseCfg('orbited_log') },
    
    { 'name': 'netserver',
      'cmd': parseCfg('netserver_command'),
      'log': parseCfg('netserver_log') },
    
    { 'name': 'gtpbot',
      'cmd': parseCfg('bot_command'),
      'log': parseCfg('bot_log') }
        
    ]


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
    
    log = "%s Starting %s: %s\n" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"), ex['name'], ex['cmd'])
    print log,
    
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
    
    proc = subprocess.Popen( args=ex['cmd'].split(' '), stdout=logfile, stderr=logfile, cwd=setcwd )
    
    # store it to our procs list
    procs.append( proc )

    
# now we dont die until all processes die
for proc in procs:
    proc.wait()

    
