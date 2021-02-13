import os
import argparse
import re

def search_string_in_file(string_to_search,read_obj):
	"""Search for the given string in file and return lines containing that string,
	along with line numbers"""
	pattern = re.compile("^\[")
	line_number = -1
	found = True
	next_found = True
	flag = True
	list_of_results = []
	# Read all lines in the file one by one
	for line in read_obj:
		# For each line, check if line contains the string
		line_number += 1
		if flag:
			if string_to_search in line:
				flag = False
				found = False
				# If yes, then add the line number & line as a tuple in the list
				list_of_results.append(line_number)
		else:
			if pattern.match(line):
				next_found = False
				list_of_results.append(line_number)
				break
	#print(list_of_results)
	#print(found)
	if found:
		raise Exception("No matches in ansible hostfile for that name")
	if next_found:
		list_of_results.append(line_number+1)
	return list_of_results

# Construct the argument parser
ap = argparse.ArgumentParser(description='Delete multiple VMs')

ap.add_argument('n', metavar='n', type=int,
   help="Number of VMs you want to create") ##done
ap.add_argument('H', metavar='H', type=str,
   help="Base hostname of the VMs, they will have hostname1-N depending on the number of VMs if -k not applied") 
ap.add_argument('-O', "--offset", type=int, default=0, required=False,
   help="Offset initial starting value for hostnamek-(k+N), default is 0") 
ap.add_argument('-a',"--ansible", help="Remove ansible hosts, it will remove all attached to the same hostname regardless of number",
	    action="store_true")

args = ap.parse_args()

names = []

for x in range(args.n):
  names.append(args.H + str(x+args.offset))

for x in range(args.n):
  os.system("VBoxManage controlvm %s poweroff" %names[x])
  os.system("VBoxManage unregistervm --delete %s" %names[x])

if args.ansible:
	fp = open("/etc/ansible/hosts", "r")
	lines = fp.readlines()
	fp.close()
	nums= search_string_in_file("[%s]\n" %args.H,lines)
	#print(nums[0])
	#print(nums[1])
	numsdel = nums[1] - nums[0]
	#print(lines[nums[0]])
	for x in range(numsdel):
		del lines[nums[0]]
	#print(lines)

	new_file = open("/etc/ansible/hosts", "w+")
	for line in lines:
		new_file.write(line)
	new_file.close()
	#del lines[nums[0]]
	#with open("/etc/ansible/hosts", "r") as fp:
	#	for line in lines_that_equal("[%s]\n" %args.H, fp):
	#		print("hola")