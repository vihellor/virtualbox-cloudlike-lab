import argparse
from ipaddress import ip_address
import os
import psutil
import subprocess
import getpass


def validateOva(v):
    if v.endswith('.ova'):
       return v
    else:
        raise argparse.ArgumentTypeError('ova file expected.')

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def readable_dir(prospective_dir):
  if not os.path.isdir(prospective_dir):
    raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
  if os.access(prospective_dir, os.R_OK):
    return prospective_dir
  else:
    raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))

# Construct the argument parser
ap = argparse.ArgumentParser(description='create multiple VMs from an Ova file')

# Add the arguments to the parser
ap.add_argument('n', metavar='n', type=int,
   help="Number of VMs you want to create")
ap.add_argument('H', metavar='H', type=str,
   help="Base hostname of the VMs, they will have hostname1-N depending on the number of VMs")
ap.add_argument("-s", "--startIp", type=ip_address, required=False,
   help="Starting ip in case you want to set the initial and following ips")
ap.add_argument("-o", "--ovaName", type=validateOva, required=False, default="centos7seed.ova",
   help="Name of the ova name, needs to be in the current directory if -d not specified")
ap.add_argument("-d", "--directory", type=readable_dir, default=os.path.dirname(os.path.realpath(__file__)), required=False,
   help="Directory to take all scripts and ovas from")
ap.add_argument("-p", "--pingNumberCheck", type=int, default=3, required=False,
   help="Number of pings to check before failing")
ap.add_argument("-t", "--timeToCheck", type=int, default=10, required=False,
   help="Time in between ping checks (seconds)")
ap.add_argument("-w", "--timeWaitReboot", type=int, default=60, required=False,
   help="Time to wait during reboot (seconds)")
ap.add_argument("-c", "--copyScripts", type=str2bool, default=False, required=False,
   help="Time to wait during reboot (seconds)")
ap.add_argument("-m", "--memory", type=int, choices=range(512, 10240), default=1024, required=False,
   help="Memory to allocate to the machine")
ap.add_argument("-C", "--cpus", type=int, choices=range(1, 10), default=1, required=False,
   help="Number of CPUs to use")

args = ap.parse_args()

print("Numbers of VM to create: ", args.n)
print("Base hostname to use: ", args.H)
print("Start Ip", args.startIp)
print("Name of the ova to use: ", args.ovaName)
print("Directory to use: ", args.directory)
print("Number of pings: ", args.pingNumberCheck)
print("Time before checking: ", args.timeToCheck)
print("Time to wait until reboot: ", args.timeWaitReboot)
print("Are we copying scripts?? ", args.copyScripts)
print("Ram memory allocated per VM: ", args.memory)
print("CPUs to allocate per VM: ", args.cpus)

#################################################################
####    validate there is enough resouces for this to run    ####
#################################################################

# gives a single float value
#cpu= psutil.cpu_percent()
cpu_num= os.cpu_count()
#cpu_load = psutil.getloadavg()
#cpu_percent = psutil.cpu_percent()

av1, av2, av3 = os.getloadavg()

#cpu_load2 = [x / os.cpu_count() * 100 for x in os.getloadavg()][-1]
# you can have the percentage of used RAM
#used_mem= psutil.virtual_memory().percent
# you can calculate percentage of available memory
#avail_mem= psutil.virtual_memory().available * 100 / psutil.virtual_memory().total
#free_mem= psutil.virtual_memory().free/1024
#avail_mem2= psutil.virtual_memory().available/(1024*1024)
#percent_mem= psutil.virtual_memory().percent

#print("the cpu data is: ",cpu,cpu_num,cpu_load,cpu_percent,cpu_load2, av1)

#print("the fre memory data is: ",free_mem,percent_mem,avail_mem2)

total_expected_mem= args.n*args.memory
total_expected_cpu= args.n*args.cpus
free_usable_mem= psutil.virtual_memory().available/(1024*1024)*0.8
free_usable_cpu= cpu_num-av1-1

print("total_expected_mem: ",total_expected_mem)
print("total_expected_cpu: ",total_expected_cpu)
print("free_usable_mem: ",int(free_usable_mem))
print("free_usable_cpu: ",int(free_usable_cpu))

if total_expected_mem > free_usable_mem:
  raise Exception("Sorry, not enough memory for all VMs") 

if total_expected_cpu > free_usable_cpu:
  raise Exception("Sorry, not enough cpus for this")

try: 
  p = getpass.getpass(prompt='ova root password: ') 
except Exception as error: 
  print('ERROR', error)

#################################################################
####    Create and start VMs    ####
#################################################################

names = []

for x in range(args.n):
  names.append(args.H + str(x))

#for x in range(args.n):
#  print(names[x])

for x in range(args.n):
  os.system("VBoxManage import %s/%s --vsys 0 --memory %s --cpus %s --vmname %s --eula accept" %(args.directory,args.ovaName,args.memory,args.cpus,names[x]))
  os.system("VBoxManage startvm %s --type=headless" %names[x])

ips = []

for x in range(args.n):
  ips.append(os.system("VBoxManage guestproperty get '%s' '/VirtualBox/GuestInfo/Net/1/V4/IP' | cut -d' ' -f2" %names[x]))
  os.system("sshpass -p '%s' ssh -o 'StrictHostKeyChecking=no' -o ConnectTimeout=3 root@%s 'hostnamectl set-hostname %s'" %(p,ips[x],names[x]))

#sshpass -p 't@uyM59bQ' ssh username@server.example.com

os.system("echo Hello from the other %s, bla bla bla %s" %(args.ovaName,free_usable_mem))

