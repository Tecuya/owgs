#!/usr/bin/env python

#####################################
# This script is provided to easily start all the necessary OWGS services 
# It is inteded to run as root.
#
# TODO clean shutdown of children processes (trap SIGKILL?)
#
######################################
# Environment initialization

import os, subprocess, traceback, pwd, sys, time, ConfigParser

os.chdir(os.path.dirname(__file__))

config = ConfigParser.ConfigParser()
config.read('daemon.cfg')

# convenient way to fetch config 
parsecfg = lambda name: config.get('owgs', name)

# Username to run OWGS as
owgs_username = parsecfg('user')

# These are the scripts we will run, and where they will be logged to
executables = [ 

    { 'name': 'devserver',
      'user': owgs_username,
      'disabled': (parsecfg('django_manage') == 'N'),
      'cmd': parsecfg('django_command'),
      'log': parsecfg('django_log') },

    { 'name': 'orbited',
      'user': 'root',
      'cmd': parsecfg('orbited_command'),
      'log': parsecfg('orbited_log') },
    
    { 'name': 'netserver',
      'user': owgs_username,
      'cmd': parsecfg('netserver_command'),
      'log': parsecfg('netserver_log') },
    
    { 'name': 'gtpbot',
      'user': owgs_username,
      'cmd': parsecfg('bot_command'),
      'log': parsecfg('bot_log') }
        
    ]


######################################
# Process launching

procs = []

for ex in executables:

    # if we were told to skip, then skip!
    if ex.has_key('disabled') and ex['disabled']:
        continue

    # attempt to seteuid 
    try:
        owgs_euid = pwd.getpwnam(ex['user'])[2]
        os.seteuid(owgs_euid)
    except Exception, e:
        print 'Failed in attempt to seteuid() to %s' % owgs_username
        traceback.print_exc()
        sys.exit()
    
    # write message indicating when the program was started to the log
    log = "%s Starting %s: %s\n" % (time.strftime("%a, %d %b %Y %H:%M:%S +0000"), ex['name'], ex['cmd'])
    print log,
    
    try:
        logfile = file(ex['log'], 'a+')        
    except Exception, e:
        print 'Could not open log file %s' % ex['log']
        traceback.print_exc()
        sys.exit()

    logfile.write(log)
    logfile.flush()

    # prepare cwd argument
    if ex.has_key('wd'):
        setcwd = ex['wd']
    else:
        setcwd = None

    # execute
    proc = subprocess.Popen( args=ex['cmd'].split(' '), stdout=logfile, stderr=logfile, cwd=setcwd )
    
    # store it to our procs list
    procs.append( proc )

    
# now we dont die until all processes die
for proc in procs:
    proc.wait()

    
