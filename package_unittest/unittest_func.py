#reference link: https://www.digitalocean.com/community/tutorials/how-to-use-unittest-to-write-a-test-case-for-a-function-in-python
#unittest.TestCase class with method to check:
    #self.assertEqual
    #self.assertTrue
    #self.assertFalse
    #self.assertRaises
#to define test cases define inheritance class of unittest.TestCase
    #each test case is method start with test
#to run test with unittest.main()
import unittest

def add_fish_to_aquarium(fish_list):
    #check length of list > 10 raise ValueError other wise return list
    if len(fish_list) > 10:
        raise ValueError("A maximum of 10 fish can be added to the aquarium")
    return {"tank_a": fish_list}


class TestAddFishToAquarium(unittest.TestCase):
    def test_add_fish_to_aquarium_success(self):
        actual = add_fish_to_aquarium(fish_list=["shark", "tuna"])
        expected = {"tank_a": ["shark", "tuna"]}
        self.assertEqual(actual, expected)

    def test_add_fish_to_aquarium_exception(self):
        too_many_fish = ["shark"] * 25
        with self.assertRaises(ValueError) as exception_context:
            add_fish_to_aquarium(fish_list=too_many_fish)
        self.assertEqual(
            str(exception_context.exception),
            "A maximum of 10 fish can be added to the aquarium"
        )

if __name__ == "__main__":
    unittest.main()

