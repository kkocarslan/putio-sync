import os
import urllib2
from datetime import timedelta
import datetime
import signal
import sys
import fcntl
import subprocess

def downloadfile(url, file_name, target_dir, size_expected, limit_rate):
  try:
    #options = "-t 10 --max-connection-per-server=4 --file-allocation=falloc --max-download-limit=900K -c -s 4 --summary-interval=20 --lowest-speed-limit=100K"
    #retcode = subprocess.call("/usr/bin/aria2c " + options + " \"" + url + "\" -d \"" + target_dir + "\" -o \"" + file_name + "\"", shell=True)
    options = "--continue --limit-rate=" + limit_rate + " --progress=dot:mega"
    cmd = "/usr/bin/wget " + options + " '" + url + "' -O '" + target_dir + "/" + file_name+"' 2>&1"
    print cmd
    retcode = subprocess.call(cmd, shell=True)
    if retcode > 0:
      print >>sys.stderr, "Child was terminated by signal", -retcode
      return False
    else:
      print >>sys.stderr, "Child returned", retcode
      return True
  except OSError as e:
    print >>sys.stderr, "Execution failed:", e
    return False
  
   
