# myls.py
# Import the argparse library
import argparse

import os
import sys

#call this script with positional argument path
# python3 package_argparse/myls.py ~/toanbui1991/python
#get help from this script with -h flag
# python3 package_argparse/myls.py -h
# Create the parser
my_parser = argparse.ArgumentParser(description='List the content of a folder')

# Add the arguments
my_parser.add_argument('Path',
                       metavar='path',
                       type=str,
                       help='the path to list')

# Execute the parse_args() method
args = my_parser.parse_args()
#get input argument
input_path = args.Path
#use input argument in your logic
if not os.path.isdir(input_path):
    print('The path specified does not exist')
    sys.exit()

print('\n'.join(os.listdir(input_path)))

#Note about optional arugment and positional argument (required)
