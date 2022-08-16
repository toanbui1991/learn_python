import subprocess

#subprocess.run() run shell process and return CompletedProcess Object
#refence link: https://docs.python.org/3/library/subprocess.html?highlight=subprocess%20run#subprocess.run
#raise error: by default subprocess will not raise error if the process error. But return CompletedProncess Object with returncode =2
#rais error with argument check=True
completed_process = subprocess.run(['python3', 'package_subprocess/timer.py', '5', 'error'], check=True)
#check the attributes of CompletedProcess Object
print('completed_process: ', completed_process)
print('completed_process args: ', completed_process.args)
#returncode = 0 means success, return code = 2 means error
print('completed_process returncode', completed_process.returncode)