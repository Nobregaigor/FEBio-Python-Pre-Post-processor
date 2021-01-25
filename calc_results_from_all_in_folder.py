from os import listdir
from os.path import isfile, join, isdir
import sys, getopt
import subprocess

def get_input_arguments(argv):
	i_folder = None
	try:
		opts, args = getopt.getopt(argv,"hi:",["ifolder="])
	except getopt.GetoptError:
		print('Error in command input. Format should be: -i <inputFolderr>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('commands: -i <inputFolder>>')
			sys.exit()
		elif opt in ("-i", "--ifolder"):
			i_folder = arg

	if i_folder == None:
		print("Input Error: No Input folder.")
		sys.exit(-1)

	return i_folder

if __name__ == "__main__":
	
	i_folder = get_input_arguments(sys.argv[1:]) # feb files folder , fiber orientation folder

	# path_to_i_folder = sys.path[0] + i_folder

	# Finding folders
	folders = [(f) for f in listdir(i_folder) if isdir(join(i_folder, f))]

	print("Number of folders found:", len(folders))
	print("List of folders to use:")
	for folder in folders:
		print("\t", folder)

	print("\n", "-"*100, "\n")

	for folder in folders:
		print("Wroking with folder:", folder,"\n")
		res = subprocess.call([
			'python.exe', 
			join(sys.path[0],'main.py'),
			'-i',
			join(i_folder,folder),
			])
		if res != 0:
			print("*"*100, "\n")
			print("Error with folder:", folder)
			print("res:",res)
			print("*"*100,"\n")

		print("\n" + "-"*100 + "\n")