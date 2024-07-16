#! /usr/bin/env python

from subprocess import Popen,PIPE
import sys
from threading import Timer
import pwd
import grp
import os


def execute_timeout(command, timeout=5):
    out = None
    err = None
    rc = -1

    kill = lambda process: process.kill()
    p = Popen(command, stdout=PIPE, stderr=PIPE, close_fds=True)
    my_timer = Timer(int(timeout), kill, [p])
    try:

        my_timer.start()
        output, err = p.communicate()
        rc = p.returncode
        p.stdout.close()
        p.stderr.close()
    finally:
        my_timer.cancel()

    return output, err, rc





def execute(command):
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    rc = p.returncode
    p.stdout.close()
    p.stderr.close()
    return output,err,rc




def execute_pipe(command):
    p = Popen(command,stdin=PIPE, stdout=PIPE, stderr=PIPE,shell=True, close_fds=True, universal_newlines=True)
    #output, err = p.communicate()
    rc = p.returncode
    #p.stdout.close()
    #p.stdout.close()
    #p.stderr.close()
    return p




