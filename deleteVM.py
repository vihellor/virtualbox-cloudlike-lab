import os
import argparse


# Construct the argument parser
ap = argparse.ArgumentParser(description='Delete multiple VMs')

ap.add_argument('n', metavar='n', type=int,
   help="Number of VMs you want to create") ##done
ap.add_argument('H', metavar='H', type=str,
   help="Base hostname of the VMs, they will have hostname1-N depending on the number of VMs if -k not applied") 
ap.add_argument('-k', "--offset", type=int, default=0, required=False,
   help="Offset initial starting value for hostnamek-(k+N), default is 0") 

args = ap.parse_args()

names = []

for x in range(args.n):
  names.append(args.H + str(x+args.offset))

for x in range(args.n):
  os.system("VBoxManage controlvm %s poweroff" %names[x])
  os.system("VBoxManage unregistervm --delete %s" %names[x])