import pytest
#in this file we have three test with three asserttion
def test_file1_method1():
	x=5
	y=6
	assert x+1 == y
	assert x == y

def test_file1_method2():
	x=5
	y=6
	assert x+1 == y
#command:
#   pytest will run all test files in folder
#   pytest file_name to run test for specific file