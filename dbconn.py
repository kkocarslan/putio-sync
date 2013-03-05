import sqlite3
import os


def connectDb():
  try:
    conn = sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + "/files.sqlite")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY)")
    conn.commit()
    return conn
  except Exception, e:
    print e
    return False


def insertFileId(file_id):
  try:
    conn = connectDb()
    c = conn.cursor()
    c.execute("INSERT INTO files VALUES (%s)" % (file_id))
    conn.commit()
    return True
  except Exception, e:
    print e
    return False

def removeFileId(file_id):
  try:
    conn = connectDb()
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE id = %s" % (file_id))
    conn.commit()
    return True
  except Exception, e:
    print e
    return False

def listFileIds():
  try:
    conn = connectDb()
    c = conn.cursor()
    c.execute("SELECT * from files")
    res = c.fetchall()
    rres = []
    for r in res:
      rres.append(r[0])
    return rres
  except Exception, e:
    print e
    return False

def checkFileId(file_id):
  try:
    conn = connectDb()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM files WHERE id = %s" % (file_id))
    count = c.fetchone()[0]
    if count > 0:
      return True
    else:
      return False
  except Exception, e:
    print e
    return False



 
    
