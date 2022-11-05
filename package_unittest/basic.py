#basic example.
#using unittest.TestCase
#this class have method like self.assertEqual, self.assertTrue, self.assertRaises
#run the test with unittest.main()
#test method of class unittest.TestCase
    #self.assertEqual()
    #self.assertTrue()
    #self.assertFalse()
    #self.assertRaises()
import unittest

#define your test case as class
class TestStringMethods(unittest.TestCase):
    #each test is a method start with test_
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()