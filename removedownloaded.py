import putio2
import os
import argparse
import ConfigParser
import signal
import fcntl
import sys
import requests
import dbconn

#
# read ini file
#
try:
  config = ConfigParser.ConfigParser()
  config.read(os.path.dirname(os.path.realpath(__file__)) + "/config.ini")
  OAUTH_KEY = config.get('putiosync', 'OAUTH_KEY')
  PUTIO_SOURCEDIR = config.get('putiosync', 'PUTIO_SOURCEDIR')
  LOCAL_TARGETDIR = config.get('putiosync', 'LOCAL_TARGETDIR')
except Exception, e:
  print "Error reading config.ini"
  print e
  sys.exit(1)

#
# prevent multiple sessions
#
lockfile = "/tmp/putioremovedownloadedfile"
fp = open(lockfile, 'w')
try:
  fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
  print "Already running"
  sys.exit(1)

#
# catch ctrl+c properly
#
def signal_handler(signal, frame):
  print "\n\n\n\nYou pressed Ctrl+C!"
  sys.exit(0)

#
# get id for the sourcedir
#
def getSourceDirId():
  try:
    return filter(lambda x: x["parent_id"] == 0, client.request("/files/search/\"" + PUTIO_SOURCEDIR  + "\" from:me type:directory/page/-1")["files"])[0]['id']
  except:
    return False

#
# get dir tree of the file
#
def getDirTree(parent_id):
  if dirNameCache.get(parent_id):
    return dirNameCache.get(parent_id)

  ppath = ""
  pparent_id = parent_id
  try:
    while pparent_id > 0:
      pfile = client.request("/files/" + str(pparent_id))["file"]
      ppath = "/" + pfile["name"] + ppath
      pparent_id = pfile["parent_id"]
    dirNameCache[parent_id] = ppath
    return ppath
  except Exception, e:
    print e

#
# remove empty dirs
#
def removeRemoteEmptyDirs(parent_id, target_base_folder):
  try:
    rfiles = client.request("/files/list?parent_id=" + str(parent_id))["files"]
    for rfile in rfiles:
      if rfile["content_type"] == "application/x-directory":
        if rfile["size"] == 0:
          print "Removing Empty Dir: /%s/%s" % (target_base_folder, rfile["name"])
          rfileUrl = client.request("/files/delete", return_url = True)
          requests.post(rfileUrl, data={'file_ids': rfile["id"]})
          return True
        else:
          removeRemoteEmptyDirs(rfile["id"], target_base_folder + "/" + rfile["name"])
  except Exception, e:
    print e
    sys.exit(1)

#
# list files
#
def removeDownloadedFiles():
  try:
    for fileId in dbconn.listFileIds():
      try:
        dfileUrl = client.request("/files/" + str(fileId), return_url = True)
        dfileResp = requests.request("GET", dfileUrl)

        if dfileResp.ok:
          dfile = dfileResp.json()["file"]

        if dfileResp.status_code == 200:
          print " + (%s) %s/%s" % (fileId, getDirTree(dfile["parent_id"]), dfile['name'])
          rfileUrl = client.request("/files/delete", return_url = True)
          if requests.post(rfileUrl, data={'file_ids': fileId}):
            dbconn.removeFileId(fileId)
            print "removed"
        elif dfileResp.status_code == 404:
          print " - (%s) Already removed: %s" % (fileId, dfileResp.status_code)
          dbconn.removeFileId(fileId)
        else:
          print " ? (%s) What?? %s" % (fileId, dfileResp.status_code)
      except Exception, e:
        print e
        continue

      #print "(%s) %s/%s" % (fileId, getDirTree(dfile["parent_id"]), dfile['name'])
      #print fileId
  except Exception, e:
    print e


if __name__=="__main__": 
  dirNameCache = {}
  signal.signal(signal.SIGINT, signal_handler)
  client = putio2.Client(OAUTH_KEY)
  sourceDirId = getSourceDirId()
  removeRemoteEmptyDirs(sourceDirId, PUTIO_SOURCEDIR)
  removeDownloadedFiles()
