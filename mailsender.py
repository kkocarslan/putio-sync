import smtplib



def sendMail(REPORT_FROM, REPORT_TO, SMTP_HOST, SMTP_USER, SMTP_PASS, subject="Download Complete", msg="yes i said complete"):
  try:
    body = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (REPORT_FROM, REPORT_TO, subject, msg)
    server = smtplib.SMTP_SSL(host=SMTP_HOST, port=465)
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(REPORT_FROM, REPORT_TO, body)
    return True
  except Exception, e:
    print "unable to send notification mail", e
    return False


