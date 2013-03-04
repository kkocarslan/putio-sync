import sys
import os
import subprocess
import atexit

def downloadfile(url, file_name, target_dir, size_expected, limit_rate):
  file_name_tmp = file_name + ".part"
  if os.path.exists(target_dir + "/" + file_name):
    print "Something might be wrong, there should not be a file named '" + file_name + "', but there is"
    return True
    
  try:
    #options = "-t 10 --max-connection-per-server=4 --file-allocation=falloc --max-download-limit=900K -c -s 4 --summary-interval=20 --lowest-speed-limit=100K"
    #retcode = subprocess.call("/usr/bin/aria2c " + options + " \"" + url + "\" -d \"" + target_dir + "\" -o \"" + file_name + "\"", shell=True)
    options = "--continue --limit-rate=" + limit_rate + " --progress=dot:mega"
    cmd = "len=0 env wget " + options + " '" + url + "' -O '" + target_dir + "/" + file_name_tmp + "' 2>&1"
    pipeoutput = "while read line; do echo \"$line\"; let \"len+=1\"; [ $(expr $len % 20) -eq 0 ] && echo  \"\n---------------\n" + file_name + "\n---------------\n\"; done"
    print cmd
    #retcode = subprocess.call(cmd, shell=True)
    popen = subprocess.Popen(cmd + "|" + pipeoutput, shell=True)
    #atexit.register(stopdownload, popen)
    retcode = popen.wait()
    if retcode == 0:
      os.rename(target_dir + "/" + file_name_tmp, target_dir + "/" + file_name)
      print >>sys.stderr, "Child returned", retcode
      return True
    else:
      print >>sys.stderr, "Child was terminated by signal", -retcode
      return False
  except OSError as e:
    print >>sys.stderr, "Execution failed:", e
    return False
  
#def stopdownload(popen):
  #print "stopping download"
  #popen.send_signal(2)
  #popen.kill()
