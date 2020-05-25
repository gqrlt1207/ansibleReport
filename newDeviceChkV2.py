import sys 
import os 
import time 
import commands 
import smtplib
import xlsxwriter
import paramiko
import downloadFile
from pexpect import *
import sendEmail
import sendEmailV2
from smtplib import SMTPException
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from email.mime.text import MIMEText
import datetime
import glob
import shutil
import json
import re
from urllib import urlopen
from pprint import pprint
import os.path
import os
import fileinput

if len(sys.argv) < 3:
  print("\n\nUsage: python newDeviceChk.py <device.list> <MaxThread>\n\n")
  quit()

try:
  os.system(">/tmp/iCheck.out")
except:
  pass

MaxThread=sys.argv[2]

#reload(sys)
#sys.setdefaultencoding( "latin-1" )

status4, output4 = commands.getstatusoutput("date")
status3, output3 = commands.getstatusoutput("ps -Af|grep newDeviceChkV1|grep -v grep|grep -v '/bin/sh'|wc -l")
status5, output5 = commands.getstatusoutput("ps -Af|grep newDeviceChkV1|grep -v grep|grep -v '/bin/sh'")
print("\n"+output5+"\n")
print("\n"+output4+"\n")
print("begin:\n"+str(output3)+"\nend.\n")
if int(output3)>1:
  print(str(output4)+"\nnewDeviceChkV1.py is running, exit!!")
  sys.exit(40)

getCurt="date +'%s'"
status,times=commands.getstatusoutput(getCurt)
timestamp2=int(times)-24*60*60
timestamp=int(times)
value=datetime.datetime.fromtimestamp(timestamp)
value2=datetime.datetime.fromtimestamp(timestamp2)
curTT=value.strftime('%m%d')
curTT2=value2.strftime('%m%d')
fileN2="server"+curTT2
fileN="server"+curTT
print("\n"+fileN+"\n")
print("\n"+fileN2+"\n")

def chkDecomList(hostname):
  decomFlag="False"
  with open("/export/home/RIMusers/bgao/retiredServer.list","r") as inFile:
    for line in inFile:
      if hostname in line:
        print("This server: "+hostname+" was decommissioned!\n")
        decomFlag="True"
        break
  return(decomFlag)

open("/tmp/jobruntime.out","w").close
def downloadHostfile(fileN,fileN2):
  if os.path.isfile("/export/home/RIMusers/bgao/"+fileN):
    fileN2=fileN
  print("\n"+fileN+"\n")
  print("\n"+fileN2+"\n")

  open("/export/home/RIMusers/bgao/host.list","w").close
  hostFile=open("/export/home/RIMusers/bgao/host.list","rw+")
  with open("/export/home/RIMusers/bgao/"+fileN2,"rb+") as serverList:
    for line in serverList:
      sp=[]
      sp=line.split(',')
      hostname=sp[1].strip()
      ipaddress=sp[2].strip()
      osType1=sp[3].strip()
      try:
        monitored=sp[5].strip()
      except:
        monitored="nodata"
      decomFlag="False"
      decomFlag=chkDecomList(hostname)
      if decomFlag=="True":
        continue
      if "nodata" in ipaddress:
        continue
      if "-rc" in hostname:
        continue
      if "no" in monitored or "No" in monitored or "NO" in monitored:
        continue
      if "Windows" in osType1:
        osType="Windows"
      elif "Solaris" in osType1:
        osType="Solaris"
      elif "AIX" in osType1:
        osType="AIX"
      elif "Red Hat" in osType1:
        osType="Linux"
      elif "VIOS" in osType1:
        osType="VIOS"
      elif "Linux" in osType1:
        osType="Linux"
      elif "nodata" in osType1:
        continue
      else:
        osType="Unix"
      print(hostname+" , "+ipaddress+" , " +osType+" , "+osType1)
      hostFile.write(hostname+","+ipaddress+"," +osType+","+osType1+","+monitored+"\n")
      hostname=""
      ipaddress=""
      osType1=""
      osType=""
  hostFile.close()

downloadHostfile(fileN,fileN2)
#sys.exit(0)

os.system("rm -f /tmp/ansible/*.out")
os.system("rm -f /tmp/ansible/ansibleresult/*.out")

with open("/export/home/RIMusers/bgao/host.list","rb+") as inFile:
  for line in inFile:
    sp=[]
    sp=line.split(',')
    hostname=sp[0]
    break
  newStart="True"
  if os.path.isfile("/tmp/ansible/ansibleresult/"+hostname+"Success.out"):
    time1=os.path.getctime("/tmp/ansible/ansibleresult/"+hostname+"Success.out")
    getCurt1="date +'%s'"
    status,time2=commands.getstatusoutput(getCurt1)
    timestamp1=int(time2)
    timeGap=48*60*60
    timeDifferent=timestamp1-int(time1)
    print(timeDifferent)
    newStart="True"
    if timeDifferent < timeGap:
      print(str(output4)+"\nThis program has been executed recently, exit!!")
      newStart="False"
  elif os.path.isfile("/tmp/ansible/ansibleresult/"+hostname+"Err.out"):
    time1=os.path.getctime("/tmp/ansible/ansibleresult/"+hostname+"Err.out")
    getCurt1="date +'%s'"
    status,time2=commands.getstatusoutput(getCurt1)
    timestamp1=int(time2)
    timeGap=48*60*60
    timeDifferent=timestamp1-int(time1)
    print(timeDifferent)
    newStart="True"
    if timeDifferent < timeGap:
      print(str(output4)+"\nThis program has been executed recently, exit!!")
      newStart="False"

if ("alldevices" in sys.argv[1] or "resume" in sys.argv[1]) and newStart=="True":
  downloadHostfile(fileN,fileN2)
  #os.system("rm -f /tmp/ansible/ansibleresult/*")
  deviceList="/export/home/RIMusers/bgao/host.list"
elif ("alldevices" in sys.argv[1] or "resume" in sys.argv[1]) and newStart=="False":
  emailFile="/tmp/pingtest.txt"
  time1=os.path.getctime(emailFile)
  getCurt1="date +'%s'"
  status,time2=commands.getstatusoutput(getCurt1)
  timestamp1=int(time2) 
  timeGap=3*24*60*60
  timeDifferent=timestamp1-int(time1)
  print(timeDifferent)
  if timeDifferent < timeGap:
    print(str(output4)+"\nThe report has been generated, and exit the program!!")
    sys.exit(10)
  list_of_files = glob.glob('/tmp/ansible/ansibleresult/*')
  latest_file = max(list_of_files, key=os.path.getctime)
  print(latest_file)
  #sys.exit(20)
  lastHostName=""
  if "Err.out" in latest_file:
    lastHostName=latest_file.replace("Err.out","").replace('/tmp/ansible/ansibleresult/','')
    syscmd="rm -f /tmp/ansible/ansibleresult/"+lastHostName+"Err.out"
    os.system(syscmd)
  elif "Success.out" in latest_file:
    lastHostName=latest_file.replace("Success.out","").replace('/tmp/ansible/ansibleresult/','')
    syscmd="rm -f /tmp/ansible/ansibleresult/"+lastHostName+"Success.out"
    os.system(syscmd)
  print(lastHostName)
  resumeFile=open("/export/home/RIMusers/bgao/host.tmp","wb+")
  startPoint="False"
  with open("/export/home/RIMusers/bgao/host.list","rb+") as inputFile:
    for line in inputFile:
      if lastHostName in line:
        startPoint="true"
        print(str(output4)+"\nFind the last server which was checked last time!")
      if startPoint=="true":
        print(line)   
        resumeFile.write(line)
    resumeFile.close()
  deviceList="/export/home/RIMusers/bgao/host.tmp"
  #sys.exit(9)
else:
  deviceList="/export/home/RIMusers/bgao/"+sys.argv[1]

serverName=""
ipAddress=""
opSys=""

def chkWinServer(serverName,ipAddress,opSys):
  outFile='/tmp/ansible/job-'+serverName+'.out'
  testCmd='curl -H "Content-Type: application/json" -X POST -u xxx:xxxx -d \'{ "inventory": 2, "credential": 4, "extra_vars": { "opSys": "Windows", "target": "'+ipAddress+'" }}\' -k -s -o '+outFile+' https://main.twrgoo.compucom.com/api/v2/job_templates/19/launch/'
  print("\n"+testCmd+"\n")
  os.system(testCmd)
  num=1
  flag="nodata"
  time.sleep(1)
  while 1:
    time.sleep(1)
    num += 1
    if int(num) > 60:
      jobid="issueFound"
      break
    try:
      output_json=json.load(open(outFile))
      jobid=output_json['job']
      print("\n"+str(jobid)+"\n")
      break
    except:
      time.sleep(1)
      continue
  return(str(jobid))


def searchResult(filename,task,jobid):
  output_json2=json.load(open(filename))
  nextpage=output_json2['next']
  result="nodata"
  flag="notFound"
  for k in output_json2['results']:
    taskname=k['task']
    hostname=k['host_name']
    stdout=k['stdout']
    if task in taskname and "10" in hostname and stdout:
      result=k['stdout']
      flag="Found"
      break
  if flag=="notFound" and "page" in nextpage:
    filename2=filename+"2"
    num=1
    while 1:
      if num > 60:
        return("nodata")
      testCmd2='curl -H "Content-Type: application/json" -X GET -u xxx:xxx  -k -s -o '+filename2+' https://main.twrgoo.compucom.com/api/v2/jobs/'+str(jobid)+'/job_events/?order_by=start_line\'&page=2\''
      print("\n"+testCmd2+"\n")
      os.system(testCmd2)
      try:
        output_json3=json.load(open(filename2))
        result2=output_json3['results']
        if result2:
          break
        else:
          print("\n result is empty: "+str(result2)+"\n")
          time.sleep(1)
          num += 1
          continue
      except:
        num += 1
        time.sleep(1)
        continue
    result="nodata"
    flag="notFound"
    output_json3=json.load(open(filename2))
    for k in output_json3['results']:
      taskname=k['task']
      hostname=k['host_name']
      result=k['stdout']
      print("\n taskname and hostname and result:"+taskname+","+str(hostname)+","+result+"\n")
      if task in taskname and "10" in hostname and result:
        result=k['stdout']
        print("\n\npage 2 search: "+result+"\n\n")
        flag="Found"
        break
      result="nodata"
  return(result)


def replaceAll(file,searchExp,replaceExp):
  for line in fileinput.input(file, inplace=1):
    if searchExp in line:
      line = line.replace(searchExp,replaceExp)
    sys.stdout.write(line)

def countFailure(jobid):  
  flag="false"
  outFile=open("/tmp/jobruntime.new","w+")
  with open("/tmp/jobruntime.out","rw+") as inFile:
    for line in inFile:
      if jobid in line:
        flag="Found"
        sp=[]
        sp=line.split(',')
        num=sp[1].strip().rstrip('\n')
        if int(num) > 300:
          f2="/tmp/ansible/ansibleresult/"+serverName+"Err.out"
          if not os.path.isfile(f2):
            oFile=open(f2,"w+")
            oFile.write("timeout"+jobid)
          testCmd2='curl -H "Content-Type: application/json" -X POST -u xxx:xxx  -k -s  https://main.twrgoo.compucom.com/api/v2/jobs/'+str(jobid)+'/cancel'
          os.system(testCmd2)
          print("\n"+testCmd2+"\n")
          time.sleep(2)
          os.system(testCmd2)
          print("\n"+testCmd2+"\n")
          oFile.close()
          flag="timeout"
        num = int(num)
        num += 1
        newline = str(sp[0])+','+str(num)+"\n"
        print("\n"+newline+"\n")
        outFile.write(newline) 
      else:
        outFile.write(line)
    if "Found" not in flag:
      outFile.write(str(jobid)+',1\n')
  outFile.close()
  os.system("mv /tmp/jobruntime.new  /tmp/jobruntime.out")
  return(flag)
    



def chkStatus(filename,serverName,ostype,jobid):
  try:
    output_json2=json.load(open(filename))
    result2=output_json2['results']
  except:
    flag="nodata"
    flag=countFailure(jobid)
    if "timeout" in flag:
      return("failed","timeout")
    else:
      return("notFound","nodata")
  if not result2:
    flag="nodata"
    flag=countFailure(jobid)
    if "timeout" in flag:
      return("failed","timeout")
    else:
      return("notFound","nodata")
  status=output_json2['results'][0]['summary_fields']['job']['status']
  result="nodata"
  flag="notFound"
  if "success" in status and "Windows" in ostype:
    task="GetWinPingResult"
    result="Ping test succeed!"
    #result=searchResult(filename,task,jobid)
    #print("\n"+str(result)+"\n")
    return("success",str(result))
  elif "fail" in status and "Windows" in ostype:
    task="Windows Ping test"
    result=searchResult(filename,task,jobid)
    result=result.encode('ascii', 'ignore')
    print("\n"+str(result)+"\n")
    return("failed",str(result))
  elif "running" in status:
    flag="nodata"
    flag=countFailure(jobid)
    if "timeout" in flag:
      return("failed","timeout")
    else:
      print("\n job status: running.\n")
      return("running",result)
  elif "success" in status and ("AIX" in ostype or "Linux" in ostype or "Solaris" in ostype):
    task="GetUnixPingResult"
    #result=searchResult(filename,task,jobid)
    result="Ping test succeed!"
    #print("\n"+str(result)+"\n")
    return("success",str(result))
  elif "fail" in status and ("AIX" in ostype or "Linux" in ostype or "Solaris" in ostype):
    task="Unix Ping test"
    result=searchResult(filename,task,jobid)
    result=result.encode('ascii', 'ignore')
    print("\n"+str(result)+"\n")
    return("failed",str(result))
  elif "success" in status and "VIOS" in ostype:
    task="GetViosPingResult"
    #result=searchResult(filename,task,jobid)
    #print("\n"+str(result)+"\n")
    result="Ping test succeed!"
    return("success",str(result))
  elif "fail" in status and "VIOS" in ostype:
    task="VIOS Ping test"
    result=searchResult(filename,task,jobid)
    result=result.encode('ascii', 'ignore')
    print("\n"+str(result)+"\n")
    return("failed",str(result))
  else:
    #print("\n"+result+"\n")
    flag="nodata"
    flag=countFailure(jobid)
    if "timeout" in flag:
      return("failed","timeout")
    else:
      return("notFound",result)



def chkServerResult(jobid,serverName,ostype):
  flag="False"
  filename='/tmp/ansible/jobResult-'+serverName+'.out'

  testCmd2='curl -H "Content-Type: application/json" -X GET -u xxx:xxxx  -k -s -o '+filename+' https://main.twrgoo.compucom.com/api/v2/jobs/'+str(jobid)+'/job_events/?order_by=start_line'
  print("\n"+testCmd2+"\n")
  os.system(testCmd2)
  time.sleep(1)
  try:
    output_json2=json.load(open(filename))
    result=output_json2['results']
  except:
    flag=countFailure(jobid)
    if "timeout" in flag:
      return("True")
    else: 
      reurn("False")
  #try:
  status,winResult=chkStatus(filename,serverName,ostype,jobid)
  #print("\n"+winResult+"\n")
  if "success" in status:
      f1="/tmp/ansible/ansibleresult/"+serverName+"Success.out"
      oFile=open(f1,"wb+")
      oFile.write(winResult)
      oFile.close()
      return("True")
  elif "fail" in status:
      f2="/tmp/ansible/ansibleresult/"+serverName+"Err.out"
      if not os.path.isfile(f2):
        oFile=open(f2,"w+")
        oFile.write("the jobid is "+jobid+" . errmsg: "+winResult)
        oFile.close()
      return("True")
  else:
      print("\n"+"Job is running"+"\n")
      return("False")

def chkUnixServer(serverName,ipAddress,opSys):
  outFile='/tmp/ansible/job-'+serverName+'.out'
  testCmd='curl -H "Content-Type: application/json" -X POST -u xxxx:xxxx -d \'{ "inventory": 2, "credential": 7, "extra_vars": { "opSys": "'+opSys+'", "target": "'+ipAddress+'" }}\' -k -s -o '+outFile+' https://main.twrgoo.compucom.com/api/v2/job_templates/19/launch/'
  print("\n"+testCmd+"\n")
  os.system(testCmd)
  #time.sleep(1)
  num=1
  while 1:
    #time.sleep(1)
    num += 1
    if int(num) > 60:
      jobid="issueFound"
      break
    try:
      output_json=json.load(open(outFile))
      jobid=output_json['job']
      print("\n"+str(jobid)+"\n")
      break
    except:
      time.sleep(1)
      continue
  return(str(jobid))


def GetResult(joblist):
  i=0
  for x in joblist:
    print(joblist)
    jobid2=""
    serverName2=""
    opSys2=""
    jobid2=x["jobid"]
    serverName2=x["servername"]
    opSys2=x["opsys"]
    print("\n"+jobid2+" "+serverName2+" "+opSys2+"\n")
    flag="False"
    flag=chkServerResult(jobid2,serverName2,opSys2)
    if flag=="True":
      joblist.pop(i)
    i += 1
  return(joblist)

workbook = xlsxwriter.Workbook('/export/home/RIMusers/bgao/reports/testDevice'+curTT+'.xlsx')
worksheet = workbook.add_worksheet("Unix")
worksheet2 = workbook.add_worksheet("Windows")
# Start from the first cell. Rows and columns are zero indexed.
bold = workbook.add_format({'bold': True})

worksheet.write(0,0, "ServerName",bold)
worksheet.write(0,1, "IPAddress",bold)
worksheet.write(0,2, "osType",bold)
worksheet.write(0,3, "TestResult",bold)
worksheet.write(0,4, "Monitored",bold)
worksheet.write(0,5, "ErrMsg",bold)

worksheet.set_column('A:D',20)
worksheet.set_column('E:E',30)
worksheet.set_column('F:F',100)

worksheet2.write(0,0, "ServerName",bold)
worksheet2.write(0,1, "IPAddress",bold)
worksheet2.write(0,2, "osType",bold)
worksheet2.write(0,3, "TestResult",bold)
worksheet2.write(0,4, "Monitored",bold)
worksheet2.write(0,5, "ErrMsg",bold)

worksheet2.set_column('A:D',20)
worksheet2.set_column('E:E',30)
worksheet2.set_column('F:F',100)

row = 1
col = 0

i=0
joblist=[]
with open(deviceList, "rb+") as inFile:
  for line in inFile:
    sp=[]
    sp=line.split(',')
    serverName=sp[0].strip()
    ipAddress=sp[1].strip()
    opSys=sp[2].strip()
    opSys1=sp[3].strip().rstrip('\n')
    try:
      monitored=sp[4].strip().rstrip('\n')
    except:
      monitored="nodata"
    b={}
    f1="/tmp/ansible/ansibleresult/"+serverName+"Err.out"
    f2="/tmp/ansible/ansibleresult/"+serverName+"Success.out"
    try:
      os.remove(f1)
      os.remove(f2)
    except:
      pass
    if 'Windows' in opSys or 'windows' in opSys: 
      jobid=""
      jobid=chkWinServer(serverName,ipAddress,opSys)
      if "issueFound" in jobid:
        print("\n Failed to get jobid for more than 1 minutes. exit.\n")
        workbook.close()
        sys.exit(2)
      b={"jobid":jobid,"servername":serverName,"opsys":opSys}
      joblist.append(dict(b))
    else:
      jobid=""
      jobid=chkUnixServer(serverName,ipAddress,opSys)
      if "issueFound" in jobid:
        print("\n Failed to get jobid for more than 1 minutes. exit.\n")
        workbook.close() 
        sys.exit(2)
        #break
      b={"jobid":jobid,"servername":serverName,"opsys":opSys}
      joblist.append(dict(b))
    i += 1
    if i >= int(MaxThread):
      while 1:
        #time.sleep(1)
        joblist=GetResult(joblist)
        i=len(joblist)
        if i < int(MaxThread):
          break 
         
  for i in range(60): 
    if len(joblist)>0:
      joblist=GetResult(joblist)
      time.sleep(20)
    else:
      break
  if len(joblist)>0:
    for k in joblist:
      jobid2=""
      serverName2=""
      opSys2=""
      jobid2=k["jobid"]
      serverName2=k["servername"]
      opSys2=k["opsys"]
      f2="/tmp/ansible/ansibleresult/"+serverName+"Err.out"
      oFile=open(f2,"wb+")
      oFile.write("Time out and jobid is: "+jobid2)
      oFile.close()
      

sp2=[]
#outFileChk=open("/home/bgao/Desktop/chkResult.csv","wb+")
#outFileChk.write("serverName"+" , "+"ipAddress"+" , "+"OS Type"+" , "+"TestResult"+" , "+"Error Message"+"\n")
colw=0
rowin=1
aixFailed=0
linuxFailed=0
solarisFailed=0
windowsFailed=0
viosFailed=0
viosTotal=0
aixTotal=0
linuxTotal=0
solarisTotal=0
windowsTotal=0
if "resume" in sys.argv[1] or "alldevices" in sys.argv[1]: 
  deviceList="/export/home/RIMusers/bgao/host.list"
with open(deviceList,"rb+") as resultFile:
  for line in resultFile:
    serName=""
    ipAddr=""
    opSys=""
    sp2=line.split(',')
    serName=sp2[0].strip()
    ipAddr=sp2[1].strip()
    opSys=sp2[3].strip()
    try:
      monitored=sp2[4].strip().rstrip('\n')
    except:
      monitored="nodata"
    fName1="/tmp/ansible/ansibleresult/"+serName+"Success.out" 
    fName2="/tmp/ansible/ansibleresult/"+serName+"Err.out"
    serNameStatus="nodata"
    ErrMsg="N/A"
    if "Windows" in opSys:
      windowsTotal += 1
    elif "Red Hat" in opSys or "Linux" in opSys:
      linuxTotal += 1
    elif "Solaris" in opSys:
      solarisTotal += 1
    elif "VIOS" in opSys:
      viosTotal += 1
    elif "AIX" in opSys:
      aixTotal += 1
    else:
      print("no proper os type found "+opSys+' '+serName)

    if os.path.isfile(fName1):
      serNameStatus="Success"
    else:
      serNameStatus="Failed"
      if "Windows" in opSys:
        windowsFailed += 1
      elif "Red Hat" in opSys:
        linuxFailed += 1
      elif "Solaris" in opSys:
        solarisFailed += 1
      elif "VIOS" in opSys:
        viosFailed += 1
      elif "AIX" in opSys:
        aixFailed += 1
      else:
        print("no proper os type found "+opSys+' '+serName)
      try:
        with open(fName2,"rb+") as outFile2:
          ErrMsg=outFile2.read().replace(',','.')
          print("\n"+ErrMsg+"\n")
      except:
        ErrMsg="no data"
    if opSys.find("Windows")!=-1:
      worksheet2.write(rowin, colw, serName)
      worksheet2.write(rowin, colw + 1, ipAddr)
      worksheet2.write(rowin, colw + 2, opSys)
      worksheet2.write(rowin, colw + 3, serNameStatus)
      worksheet2.write(rowin, colw + 4, monitored)
      worksheet2.write(rowin, colw + 5, ErrMsg)
      rowin += 1
    else:
      worksheet.write(row, col, serName)
      worksheet.write(row, col + 1, ipAddr)
      worksheet.write(row, col + 2, opSys)
      worksheet.write(row, col + 3, serNameStatus)
      worksheet.write(row, col + 4, monitored)
      worksheet.write(row, col + 5, ErrMsg)
      row += 1

    print(serName+" , "+ipAddr+" , "+opSys+" , "+serNameStatus+" , "+str(ErrMsg)) 
    #outFileChk.write(serName+" , "+ipAddr+" , "+opSys+" , "+serNameStatus+" , "+ErrMsg+"\n")
#outFileChk.close()
worksheet.autofilter('A1:F150')
worksheet2.autofilter('A1:F150')
workbook.close()

totalHost=aixTotal+viosTotal+solarisTotal+linuxTotal+windowsTotal
totalFailed=aixFailed+viosFailed+solarisFailed+linuxFailed+windowsFailed

subj="Ansible ping test report"
if "host.list" in deviceList:
  eFile=open('/tmp/pingtest.txt','w+')
  efile="/tmp/pingtest.txt"
  #os.system("rm -f  /tmp/ansible/ansibleresult/*")
  #print("purge all middle files!!\n")
else:
  eFile=open('/tmp/pingtemp.txt','w+')
  efile="/tmp/pingtemp.txt"
eFile.write("Hi team:\n\n")
eFile.write("  "+str(totalHost)+" servers were checked , "+str(totalFailed)+" servers failed the Ansible Ping Test.\n")
eFile.write("  Below is the details:\n")
eFile.write("  Total AIX servers: "+str(aixTotal)+ ". \n")
eFile.write("    not Ansible ready: "+str(aixFailed)+". \n")
eFile.write("  Total VIOS servers: "+str(viosTotal)+". \n")
eFile.write("    not Ansible ready: "+str(viosFailed)+". \n")
eFile.write("  Total Solaris servers: "+str(solarisTotal)+". \n")
eFile.write("    not Ansible ready: "+str(solarisFailed)+". \n")
eFile.write("  Total Linux servers: "+str(linuxTotal)+". \n")
eFile.write("    not Ansible ready: "+str(linuxFailed)+". \n")
eFile.write("  Total Windows servers: "+str(windowsTotal)+". \n")
eFile.write("    not Ansible ready: "+str(windowsFailed)+". \n\n")
eFile.write("Thanks and Regards. \n")
eFile.close()

att=['/export/home/RIMusers/bgao/reports/testDevice'+str(curTT)+'.xlsx']
#sendEmailV2.sendEmail(subj,efile,att,"bill.gao@compucom.com")
sendEmail.sendEmail(subj,efile,att,"bill.gao@compucom.com","Camilo.Leite@compucom.com","dilvan.karunaratne@compucom.com","Kevin.Zhao@compucom.com","Forth.Kuo@compucom.com","luis.vegavelarde@compucom.com","Andre.Kottier@compucom.com","Uriel.Caballero@compucom.com","Fernando.Garcia@compucom.com","Matthew.Riding@compucom.com","Chad.Cable@compucom.com","Jon.Carr@compucom.com","Juan.Abundis@compucom.com","Horacio.Chavez@compucom.com")
