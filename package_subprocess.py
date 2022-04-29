import subprocess

#subprocess is a python package which help you call os command from python
#subprocess call method, shell=True take input as string which is as you type command in the console
#by default the out put of command will print to console
# subprocess.run('ls -a', shell=True)
process = subprocess.run(['echo', '$HOME'], shell=True, capture_output=True, text=True)
print('HOME: {}'.format(process.stdout))