import unittest

from .breeze_test import BreezeApiTestCase


def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BreezeApiTestCase))
    return suite
