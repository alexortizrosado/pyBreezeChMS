import unittest

from .breeze_test import BreezeApiTestCase
from .profile_helper_test import HelperTests, DiffTests

def all_tests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BreezeApiTestCase))
    suite.addTest(unittest.makeSuite(HelperTests))
    suite.addTest(unittest.makeSuite(DiffTests))
    return suite