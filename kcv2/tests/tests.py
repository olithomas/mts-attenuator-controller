'''
Created on 6 Oct 2015

@author: LTE5
'''
import unittest
from kcv2.server.stubServer import StubServer
from kcv2 import kcv2
import time
        #sys.argv.append('-q') # Simple Query
        #for s in '-q -a 1 -b 2'.split(' '): sys.argv.append(s) # Illegal query
        #for s in '-a 35 35 35 -b 6 2 3'.split(' '): sys.argv.append(s) # SImple static
        #for s in '-a 1 2 3 -b 3 4 6'.split(' '): sys.argv.append(s) # Multiple static
        #for s in '-a 2 3 -b 3 7'.split(' '): sys.argv.append(s) # Illegal static (out of range)
        #for s in '-a 2 4 3 -b 3 6'.split(' '): sys.argv.append(s) # Illegal static (incorrect number of arguments)
        #for s in '-a -45 3 -b 3 2'.split(' '): sys.argv.append(s) # Illegal static (out of range)
        #for s in '-a 20 20 -b 3 2 -t 10 10'.split(' '): sys.argv.append(s) # Simple relative ramp
        #for s in '-a -20 -10 -b 3 2 -t 10 5'.split(' '): sys.argv.append(s) # Mixed relative ramp
        #sys.argv.extend('-a -20 -10 -b 3 2 -t 10 5'.split(' '))
        #for s in '-a -94 2 -b 3 2 -t 5'.split(' '): sys.argv.append(s) # Illegal relative ramp (out of range)
        #for s in '-a 20 20 -b 1 2 -t 10 10 -i 0 0'.split(' '): sys.argv.append(s) # Simple absolute ramp
        #for s in '-a -1 2 -b 3 2 -t 5 -i 34 56'.split(' '): sys.argv.append(s) # Illegal absolute ramp (out of range)
        #for s in '-a 1 2 -b 3 2 -t 5 -i 34 56 43'.split(' '): sys.argv.append(s) # Illegal absolute ramp (incorrect number of arguments)

DEBUG = 0

class TestKc(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestKc, cls).setUpClass()
        if DEBUG: print '** Test Class: creating the stubServer'
        cls.__server = StubServer()
        if DEBUG: print '** Test Class: starting the server'
        cls.__server.start()
        if DEBUG: print '** Test Class: server started'

    @classmethod
    def tearDownClass(cls):
        super(TestKc, cls).tearDownClass()
        cls.__server.terminate()

    def test_static_multi_bts(self):
        if DEBUG: print '** Test Class: starting test test_static_multi_bts'
        argsToTest = '-b 6 2 5 -a 43 34 53'
        exEndState = [35,34,35,93,53,43]
        
        kcv2.main(argsToTest.split(' '))
        time.sleep(0.1)
        endState = self.__server.getState()
        if DEBUG: print '** Test Class: running assertion for test_static_multi_bts'
        self.assertEqual(endState, exEndState)
        
    def test_checkServerWorking(self):
        if DEBUG: print '** Test Class: starting test test_checkServerWorking'
        argsToTest = '-b 1 2 3 -a 35 35 35'
        exEndState = [35,35,35,93,93,93]
        
        kcv2.main(argsToTest.split(' '))
        time.sleep(0.1)
        endState = self.__server.getState()
        if DEBUG: print '** Test Class: running assertion for test_checkServerWorking'
        self.assertEqual(endState, exEndState)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()