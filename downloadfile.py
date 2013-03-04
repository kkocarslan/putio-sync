import os
import urllib2
from datetime import timedelta
import datetime
import signal
import sys
import fcntl
import subprocess

def downloadfile(url, file_name, target_dir, size_expected):
  try:
    #options = "-t 10 --max-connection-per-server=4 --file-allocation=falloc --max-download-limit=900K -c -s 4 --summary-interval=20 --lowest-speed-limit=100K"
    #retcode = subprocess.call("/usr/bin/aria2c " + options + " \"" + url + "\" -d \"" + target_dir + "\" -o \"" + file_name + "\"", shell=True)
    options = "--continue --limit-rate=1500k --progress=dot:mega"
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
  

def downloadfile2(url, file_name, target_dir, size_expected):
  file_path_orig = target_dir + "/" + file_name 
  if os.path.exists(file_path_orig):
    return True
  file_path = file_path_orig + ".putiopart"

  if os.path.exists(file_path) and os.path.getsize(file_path) >= size_expected:
    os.rename(file_path, file_path_orig)
    return True
  
  try:
    req = urllib2.Request(url)
    if os.path.exists(file_path):
        f = open(file_path, 'ab')
        file_size_dl = os.path.getsize(file_path)
        req.add_header("Range","bytes=%s-" % (file_size_dl))
    else:
        f = open(file_path, 'wb')
        file_size_dl = 0

    initial_file_size = file_size_dl
    u = urllib2.urlopen(req, timeout = 30)
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0]) + file_size_dl
    if file_size_dl >= file_size:
        print "File %s already downloaded (%s)" % (file_name, file_size)
        return True
    if initial_file_size > 0:
        print "Resuming: %s Bytes %s" % (file_name, file_size)
    else:
        print "Downloading: %s Bytes %s" % (file_name, file_size)
    start_time = datetime.datetime.now()
    print start_time
    block_sz = 48 * 1024
    while True:
      buffer = u.read(block_sz)
      if not buffer:
          break
      
      elapsed = datetime.datetime.now() - start_time 
      hours, remainder = divmod(elapsed.seconds, 3600)
      minutes, seconds = divmod(remainder, 60)
      
      elapsed_seconds = elapsed.seconds if elapsed.seconds > 0 else 1  
      size_per_second = ((file_size_dl - initial_file_size)/1000) / elapsed_seconds
      
      file_size_dl += len(buffer)
      f.write(buffer)
      status = r"%10d  [%3.2f%%] - time since start '%sh%sm%ss'  -  %3.2fkB/s                       " % (file_size_dl, file_size_dl * 100. / file_size, hours, minutes, seconds, size_per_second)
      status = status + chr(8)*(len(status)+1)
      print status,

    if file_size_dl >= file_size:
      os.rename(file_path, file_path_orig)
      return True
    else:
      return False

  except Exception, e: 
    print e
    return False
  finally:
    f.close()
    
