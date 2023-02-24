#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from context import rosetta
import unittest
import os
import sys

#print("test_evalute executing")
#sys.path.insert(0,  os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

#import rosetta
#from rosetta.scripts.run import main
#import rosetta.runner


class TestStringMethods(unittest.TestCase):
    def test_upper2(self):
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
