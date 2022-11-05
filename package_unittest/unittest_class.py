import os
import unittest

class AdvancedFishTank:
    def __init__(self):
        self.fish_tank_file_name = "fish_tank.txt"
        default_contents = "shark, tuna"
        with open(self.fish_tank_file_name, "w") as f:
            f.write(default_contents)

    def empty_tank(self):
        os.remove(self.fish_tank_file_name) #remove file name


class TestAdvancedFishTank(unittest.TestCase):
    #using setUp method
    #why using setUp method
        #setUp will run before each test case run.
        #setUp will create resource which will used in all test case. In this case fish_tank attributes
    def setUp(self):
        self.fish_tank = AdvancedFishTank()
    #using tearDown method will cause after each test cases run to clean up what test case have affect
    #tearDown to clean up after each test run. in this case we remove file created by test case
    def tearDown(self):
        self.fish_tank.empty_tank()

    def test_fish_tank_writes_file(self):
        with open(self.fish_tank.fish_tank_file_name) as f:
            contents = f.read()
        self.assertEqual(contents, "shark, tuna")