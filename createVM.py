import argparse
from ipaddress import ip_address
import os
import psutil
import getpass
import time
from shlex import split

def validateOva(v):
    if v.endswith('.ova'):
       return v
    else:
        raise argparse.ArgumentTypeError('ova file expected.')

def printv(v,m):
    if v:
       print(m)

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

def checkIPS(name,attemps,waitTime):
  for x in range(attemps):
    cp = os.popen("VBoxManage guestproperty get '%s' '/VirtualBox/GuestInfo/Net/1/V4/IP' | cut -d' ' -f2" %name).read()
    #print("++"+cp+"++")
    if (cp != "value\n"):
      return cp.rstrip('\n');
    else:
      time.sleep(waitTime)
  raise argparse.ArgumentTypeError('No connection to:  %s'%name)

def search_string_in_file(string_to_search,read_obj):
  line_number = -1
  found = False
  list_of_results = []
  for line in read_obj:
    line_number += 1
    if string_to_search in line:
      found = True
      break
  list_of_results.append(found)
  list_of_results.append(line_number)
  #print(list_of_results)
  return list_of_results

# Construct the argument parser
ap = argparse.ArgumentParser(description='create multiple VMs from an Ova file')

# Add the arguments to the parser
ap.add_argument('n', metavar='n', type=int,
   help="Number of VMs you want to create") ##done
ap.add_argument('H', metavar='H', type=str,
   help="Base hostname of the VMs, they will have hostname1-N depending on the number of VMs if -k not applied") 
ap.add_argument("-s", "--startIp", type=ip_address, required=False,
   help="Starting ip in case you want to set the initial and following ips")
ap.add_argument("-o", "--ovaName", type=validateOva, required=False, default="centos7seed.ova",
   help="Name of the directory where the ova and script directory will be located, needs to be in the current directory if -d not specified") ##done
ap.add_argument("-d", "--directory", type=readable_dir, default=os.path.dirname(os.path.realpath(__file__)), required=False,
   help="Directory to take all scripts and ovas from")
ap.add_argument("-p", "--pingNumberCheck", type=int, default=5, required=False,
   help="Number of pings to check before failing")
ap.add_argument("-t", "--timeToCheck", type=int, default=10, required=False,
   help="Time in between ping checks (seconds)")
ap.add_argument("-w", "--timeWaitReboot", type=int, default=60, required=False,
   help="Time to wait during reboot (seconds)")
ap.add_argument("-c", "--copyScripts", type=str2bool, default=False, required=False,
   help="Copy scripts into VMs drom scripts directory")
ap.add_argument("-m", "--memory", type=int, choices=range(512, 10240), default=512, required=False,
   help="Memory to allocate to the machine") ##done
ap.add_argument("-C", "--cpus", type=int, choices=range(1, 10), default=1, required=False,
   help="Number of CPUs to use") ##done
ap.add_argument('-O', "--offset", type=int, default=0, required=False,
   help="Offset initial starting value for hostnamek-(k+N), default is 0")
ap.add_argument("--verbose", help="Increase output verbosity",
                    action="store_true")
ap.add_argument('-a',"--ansible", help="Add hosts for ansible",
                    action="store_true")
ap.add_argument('-k',"--keys", help="Generate ssh keys to devices",
                    action="store_true")

args = ap.parse_args()
VMnumber = args.n+args.offset

print("Numbers of VM to create: ", args.n)
print("General number in hostname: from %s to %s" %(args.offset,VMnumber-1))
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

total_expected_mem= VMnumber*args.memory
total_expected_cpu= VMnumber*args.cpus
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

#################################################################
####    validate there are no other VMs with the same name   ####
#################################################################

names = []

for x in range(args.n):
  names.append(args.H + str(x+args.offset))

for x in range(args.n):
  result = os.system("VBoxManage list vms | grep %s" %names[x])
  if (result == 0):
    raise Exception("device name %s is already in use" %names[x])


#################################################################
####    if no issues ask for the root password of the ova    ####
#################################################################

try: 
  p = getpass.getpass(prompt='ova root password: ') 
except Exception as error: 
  print('ERROR', error)

#################################################################
####               Create and start VMs                      ####
#################################################################

#for x in range(args.n):
#  print(names[x])

for x in range(args.n):
  #print("VBoxManage import %s/%s --vsys 0 --memory %s --cpus %s --vmname %s --eula accept" %(args.directory,args.ovaName,args.memory,args.cpus,names[x]))
  
  if args.verbose:
    os.system("VBoxManage import %s/%s --vsys 0 --memory %s --cpus %s --vmname %s --eula accept" %(args.directory,args.ovaName,args.memory,args.cpus,names[x]))
  else:
    os.system("VBoxManage import %s/%s --vsys 0 --memory %s --cpus %s --vmname %s --eula accept &>/dev/null" %(args.directory,args.ovaName,args.memory,args.cpus,names[x]))
  os.system("VBoxManage startvm %s --type=headless" %names[x])

#################################################################
####               Wait for VMs to start                     ####
#################################################################

#print("Waiting on VMs to power on")
#time.sleep(args.timeToCheck)

#################################################################
####          Change hostname directly on VM                 ####
#################################################################

ips = []

print("Checking ips")

for x in range(args.n):
  ips.append(checkIPS(names[x],args.pingNumberCheck,args.timeToCheck))

print("IPs of the devices: ", ips)

time.sleep(args.timeToCheck)

print("Changing hostnames")

for x in range(args.n):
  os.system("sshpass -p '%s' ssh -o 'StrictHostKeyChecking=no' root@%s 'hostnamectl set-hostname %s'" %(p,ips[x],names[x]))

#################################################################
####                Copy scripts to VM                       ####
#################################################################

if args.copyScripts:
  print("Copying scripts to devices")
  for x in range(args.n):
    os.system("sshpass -p '%s' scp -r %s/scripts root@%s:/root/" %(p,args.directory,ips[x]))

#################################################################
####              Generate Keys to devices                   ####
#################################################################

if args.keys:
  print("Copying ssh key")
  for x in range(args.n):
    os.system("sshpass -p '%s' ssh-copy-id -i ~/.ssh/id_rsa.pub root@%s &>/dev/null" %(p,ips[x]))

#################################################################
####        Add devices to hosts ansible files               ####
#################################################################

if args.ansible:
  print("Adding ansible hosts")

  fp = open("/etc/ansible/hosts", "r")
  lines = fp.readlines()
  fp.close()
  nums= search_string_in_file("[%s]\n" %args.H,lines)
  #print(nums[0])
  #print(nums[1])
  #print(lines[nums[1]])
  #print("[%s]"%args.H)
  p = 1
  if not nums[0]:
    lines.insert(nums[1]+p, "[%s]\n"%args.H)
    p = 2
  lines.insert(nums[1]+p, "#%s from %s to %s\n"%(args.H,args.offset,VMnumber-1))
  for x in range(args.n):
    lines.insert(nums[1]+p+1+x, "%s\n"%ips[x])
    #print(ips[x])
  #print(lines)
  f = open("/etc/ansible/hosts", "w")
  lines = "".join(lines)
  f.write(lines)
  f.close()
  #numsdel = nums[1] - nums[0]
  #print(lines[nums[0]])
  #for x in range(numsdel):
  #  del lines[nums[0]]
  #print(lines)

  #new_file = open("/etc/ansible/hosts", "w+")
  #for line in lines:
  #  new_file.write(line)
  #new_file.close()
  #print("[%s]"%args.H)
  #for x in range(args.n):
  #  print(ips[x])


#################################################################
####        Change ip directly on VMs and restart            ####
#################################################################



#################################################################
####                      check                              ####
#################################################################

#os.system("echo Hello from the other %s, bla bla bla %s" %(args.ovaName,free_usable_mem))