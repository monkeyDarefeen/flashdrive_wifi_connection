import csv
import sys
import time
from xmlrpc.client import SYSTEM_ERROR
import pyudev
import subprocess
import os


def main():
    username = subprocess.getstatusoutput("echo $USER")[1]
    directory= "/media/{0}/".format(username)
    forget_previous_network = 1
    os_pendrives = []   
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')
    monitor.start()

    for device in iter(monitor.poll, None):
        print(device)
        time.sleep(5)
        try:
            os_pendrives = get_all_usb_devices(directory)
        except Exception as e:
            print("os_pendrive read error",e)
        try:
            ssid_pass = search_for_file(directory, os_pendrives)
        except Exception as e:
            print("ssd_passd file read error",e)
        try:
            if check_duplicity(ssid_pass[0],ssid_pass[1]):
                pass
            else:
                connect_wifi(ssid_pass[0],ssid_pass[1],forget_previous_network)
        except Exception as e:
            print("wifi connection error",e)


def get_all_usb_devices(directory):
    lst= []
    for root, dirs, files in os.walk(directory):
        for directory in dirs:
            lst.append(directory)
            print(directory)
        break
    return lst

def search_for_file(directory,os_pendrives):
    for devices in os_pendrives:
            for root, dirs, files in os.walk(directory+"/"+devices):
                for filename in files:
                    if filename == "wifi.txt":
                        file_path = directory+"/"+devices+"/"+filename
                        with open(file_path,"r") as f:
                            lines = f.readlines()
                            ssid = lines[0].strip()
                            pswd = lines[1].strip()
                            return [ssid,pswd]
    return [None,None]

def forget_all_connection(ssid,pswd):
    res = subprocess.getstatusoutput("nmcli -t -f TYPE,UUID con")
    lines = res[1].split('\n')

    for line in lines:
        parts = line.split(":")
        if (parts[0] == "802-11-wireless"):
            os.system("nmcli connection delete uuid "+ parts[1])
    print (">> Done.")
    os.system("nmcli connection")
    time.sleep(3)
    command = subprocess.check_output("nmcli dev wifi connect {0} name {1} password {2}".format(ssid,ssid,pswd), shell=True)
    if "successfully" in str(command):
        print("forgetting all connection, new connection complete.") 
        
def connect_wifi(ssid,pswd,forget_network):
    os.system("nmcli radio wifi off")
    time.sleep(2)
    os.system("nmcli radio wifi on")
    time.sleep(6)
    command = subprocess.check_output("nmcli dev wifi connect {0} name {1} password {2}".format(ssid,ssid,pswd), shell=True)

    if "successfully" in str(command):
        print("command executed complete")
        if forget_network:
            try:
                forget_all_connection(ssid,pswd)
            except Exception as E:
                print("old network forget failed!!!")
        save_ssid_pass(ssid,pswd)
       # sys.exit(1)
    else:
        load_old_ssid()          

def save_ssid_pass(ssid,pswd):
    with open("ssid.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow([ssid,pswd])

def check_duplicity(ssid,pswd):
    print("checkoing for duplicity")
    try:
        with open("ssid.csv",'r') as f:
                for line in f:
                    line = line.split(",")
                    ssid_old = str(line[0]).strip()
                    pswd_old = str(line[1]).strip()
                    print("old SSID PSWD", ssid,pswd)
    
        if (ssid_old==ssid and pswd==pswd_old) or (ssid==None and pswd==None):
            print("mached")
            return True
        else:
            print(ssid_old==ssid, ssid, ssid_old)
            print(pswd_old==pswd, len(pswd), len(pswd_old))
            print("not matched")
            return False
    except Exception as E:
        print("old data not found",E)

def load_old_ssid():
    try:
        with open("ssid.csv",'r') as f:
            for line in f:
                line = line.split(",")
                ssid = str(line[0])
                pswd = str(line[1])
            command = subprocess.check_output("nmcli dev wifi connect {0} name {1} password {2}".format(ssid,ssid,pswd), shell=True)
            if "successfully" in str(command):
              #  sys.exit(1)
              pass
            else:
                print("OLD WIFI NOT CONNECTED or OLD DATA NOT FOUND")
    except Exception as e:
        print(e,"no old data found")

if __name__ == '__main__':
    main()