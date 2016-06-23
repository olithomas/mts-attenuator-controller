'''
Created on 8 Oct 2015

@author: LTE5
'''

import socket
import re
from multiprocessing import Process, Array

DEBUG = 0

class StubServer(Process):
    '''
    classdocs
    '''

    __port = 4001
    __addr = '' # all addresses 0.0.0.0
    __sock = None
    __initState = []
    __state = []
    __btsRegex = None
    __attRegex = None
    __messageRegex = None

    def __init__(self, port=4001, initState=[93,93,93,93,93,93]):
        '''
        Constructor
        '''
        super(StubServer, self).__init__()
        '''
        Once new process is spawned, instance variables remain in the parent process,
        so a multiprocessing.Array is used to share the state of the Koppelfeld and allow
        getSTate() to return the current state of the spawned process. 
        '''
        self.__port = port
        self.__state = Array('i', initState)
        self.__initState = initState
        self.__messageRegex = re.compile('R\d+P\d+')
        self.__btsRegex = re.compile('(?<=R)\d+')
        self.__attRegex = re.compile('(?<=P)\d+')
        return
    
    def run(self):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.bind((self.__addr, self.__port))
        self.__sock.listen(1)
        
        waitingForConnection = True
        '''
        Main loop will continue until process is terminated. if a connection is closed, the loop returns
        to the start and waits for a new connection. This means multiple tests can be run with the same server
        '''
        while 1:
            if DEBUG: print 'main loop started'
            if waitingForConnection:
                waitingForConnection = False
                if DEBUG: print 'waiting for a connection..'
                conn, addr = self.__sock.accept()
                if DEBUG: print 'connection received from ' + str(addr)
            chunk = ''
            chunks = []
            while '\x03' not in chunk:
                if DEBUG: print 'waiting to receive a message'
                chunk = conn.recv(8192)
                if DEBUG: print 'new message received: ' + chunk
                if not chunk:
                    if DEBUG: print 'connection terminated (if not chunk == True)'
                    waitingForConnection = True
                    break
                chunks.append(chunk)
                if DEBUG: print 'chunk appended, new chunks: ' + ''.join(chunks)
            if DEBUG: print 'no more chunks, full message: ' + ''.join(chunks)
            message = ''.join(chunks)
            if message == '\x02ST\x03':
                if DEBUG: print 'ST received, sending status'
                state = self.getState()
                stateMess = '\x02'
                for i in range(6):
                    stateMess = stateMess + 'R' + str(i+1) + 'P' + str(state[i])
                stateMess = stateMess + '\x03'
                conn.send(stateMess)
            elif self.__messageRegex.search(message) is not None:
                if DEBUG: print 'setting message received'
                it = self.__messageRegex.finditer(message)
                for m in it:
                    if DEBUG: print 'match found: ' + m.group(0) + ', running __updateState__'
                    self.__updateState__(m.group(0))
            if DEBUG: print 'message processing finished'
        conn.close()
        return
    
    def getState(self):
        with self.__state.get_lock():
            return self.__state[:6]
    
    def __updateState__(self, message):
        if DEBUG: print '__updateState__ started'
        btsNum = int(self.__btsRegex.search(message).group(0))
        attNum = int(self.__attRegex.search(message).group(0))
        if DEBUG: print 'bts num extracted: ' + str(btsNum) + ', att num extracted: ' + str(attNum)
        with self.__state.get_lock():
            if DEBUG: print 'old state: ' + str(self.__state[:6])
            self.__state[btsNum-1] = attNum
            if DEBUG: print 'new state: ' + str(self.__state[:6])
        return
        