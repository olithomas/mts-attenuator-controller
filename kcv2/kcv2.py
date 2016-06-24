#!/usr/local/bin/python2.7
# encoding: utf-8
'''
<doc_split>
kcv2 -- kc.py controls the Standard Koppelfeld SCF 0300 Variable Attenuator, fitted with the XPort Serial over LAN adapter installed
<doc_split>
Kcv2 Manual Page v1
==========================================================================
kcv2 controls the Standard Koppelfeld SCF 0300 Variable Attenuator, fitted with the XPort Serial over LAN adapter installed. 
The XPort Serial over LAN adapter (the XPort) allows the RS232 Serial commands that control the attenuator to be delivered 
to it via a TCP connection, hence making the control of the attenuator much simpler over a network. Once a TCP connection is 
set up to the XPort, the serial commands may be transferred to the attenuator over it as ASCII.
The serial commands that control the attenuator follow an extremely simple protocol explained in the User Manual of the 
attenuator (\\\\172.21.19.17\lte\Test Environment\Koppelfeld).

The attenuator is composed of six channels, herein called 'BTS' which are numbered from 1 to 6. Each BTS can support an attenuation
value of between 1 and 93 dB.

The script is able to perform concurrent operations on multiple BTS. Each argument (excluding -q -m and -h) accepts a list of numbers, 
separated by spaces.
The i-th element of each list refers to the parameters for the operation to be performed on the i-th BTS. To illustrate: 
Parameters passed:
---------------------------------------------------------------------------
-b 1 2 3
-a -10 10 20
-t 5 30 10

As -b -a and -t are specified this is a relative ramping operation (see below). The following operations will be completed as a result:
Operations completed:
---------------------------------------------------------------------------
- BTS 1 attenuation value will be reduced by 10 over 5 seconds
- BTS 2 attenuation value will be increased by 10 over 30 seconds
- BTS 3 attenuation value will be increased by 20 over 10 seconds

Each of these operations will run concurrently. That is: they will all start at the same time (although they may not finish at the same
time, depending on the values set in the -t option).

The mention of a 'relative ramping operation' in the previous paragraph now requires some explanation.
The script accepts 5 primary arguments and the presence, or not, of these arguments determines the operation requested. Briefly,
these operations are described as follows:
---------------------------------------------------------------------------
- -q option only - Query only, prints the current value of the attenuation set and exits;
- -b -a options only - Static operation, sets the attenuation values of the BTS' specified;
- -b -a -t options only - Relative ramping operation, moves the attenuation values of the BTS' specified in the -b option by the relative
offsets specified in the -a option over the times specified in the -t option;
- -b -a -t -i options - Absolute ramping operation, moves the attenuation values of the BTS' specified in the -b option from the initial
values specified in the -i option, the obsolute target values specified in the -a option over the times specified in the -t option.

In a ramping operation, the attenuation value is incremented by one at each time step. The duration of a time step is determined by the
total operation time and the difference between initial and target values. All this is calculated automatically by the script leaving
the user to only have to specify the parameters as described above.
<doc_split>
Version Tracking:
Version number        Date        Originator        Notes
-----------------------------------------------------------------------------------------------------------------------------
1.0                   23/07/2013  Oliver Thomas   Sets up a single TCP socket and sends one command before closing the socket
2.0                   25/07/2013  Oliver Thomas   Added ramping function. General tidy up etc.
3.0                   06/09/2013  Oliver Thomas   Complete re-write in current format
<doc_split>

It defines main()

@author:     Oliver Thomas

@copyright:  2015 Oli Industries. All rights reserved.

@license:    GPL

@contact:    oliver.thomas@ee.co.uk
@deffield    updated: 02/10/2015
<doc_split>
'''

DEBUG = 0 # Print debug information to the command line
TESTRUN = 0 # unit testing is running the script, don't query __main__

import sys
import os
import socket
import time
import math
from socket import error as socket_error
import re

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 3.0
__date__ = '2015-10-06'
__updated__ = '2015-10-06'

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "CLI Error: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)
    
    sock = None

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    if TESTRUN:
        program_shortdesc = 'Testing'
        program_man_page = 'Testing'
    else:
        program_shortdesc = __import__('__main__').__doc__.split("<doc_split>")[1]
        program_man_page = __import__('__main__').__doc__.split("<doc_split>")[2]
    program_license = '''%s

  Created by Oliver Thomas on %s.
  Copyright 2015 Oli Industries. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-m', '--man', action='store_true', help='Print the manual page and exit')
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-q', action='store_true', help='Print the current attenuation values and exit')
        parser.add_argument('-b','--bts',type=int,nargs='+',help='The BTS number(s) you want to change')
        parser.add_argument('-a','--attenuation',type=int,nargs='+',help='Either relative offset(s) from existing attenuation values (no -i option) or absolute target attenuation value(s) (with -i option)')
        parser.add_argument('-i','--initial',type=int,nargs='+',help='Initial attenuation value(s) to apply ramping from (for absolute ramping option only) specified for each BTS in -bts option')
        parser.add_argument('-t','--time',type=int,nargs='+',help='The timeList(s) within which to complete the ramping operation (in seconds) specified for each BTS in -bts option')
        parser.add_argument('-d','--destination',default='192.168.1.1',help='The IP address of the Koppelfeld (if different. Default=192.168.1.1)')
        parser.add_argument('-p','--port',default=4001,type=int,help='The TCP port number of the Koppelfeld (if different. Default=4001)')

        # Process arguments
        args = parser.parse_args()
        
        # If user specified -m or --man option, show the manual page and exit
        if args.man:
            print (program_man_page)
            parser.print_help()
            return 0
        
        # Assign arguments to local variables
        query = args.q
        btsList = args.bts
        attList = args.attenuation
        initList = args.initial
        timeList = args.time
        ipAddr = args.destination
        port = args.port
        
        '''
        In order to validate the correct combination of arguments, the relevant arguments for testing are converted to boolean
        Then they are grouped to form a binary number and converted to integer.
        Each integer result is given either an error message or a name if it is valid (in a dict structure).
        '''
        btsPresent = btsList is not None
        attPresent = attList is not None
        initPresent = initList is not None
        timePresent = timeList is not None
        
        argCombo = int(query)*16+int(btsPresent)*8+int(attPresent)*4+int(initPresent)*2+int(timePresent)*1
        
        # Errors and valid case names from argCombo integer
        argDict = {0 : 'Argument Combination Error: At least one argument must be provided'}
        argDict.update(dict.fromkeys(range(1, 12), 'Argument Combination Error: If not a query then at least bts and attenuation values must be set'))
        argDict.update({14 : 'Argument Combination Error: If an initial value is provided, then a timeList must also be provided'})
        argDict.update(dict.fromkeys(range(17, 32), 'Argument Combination Error: No other arguments are valid with query (-q)'))
        argDict.update({12 : 'static'}) # query = False, btsList is present, attList is present
        argDict.update({13 : 'relativeRamp'}) # query = False, btsList is present, attList is present, timeList is present
        argDict.update({15 : 'absoluteRamp'}) # query = False, btsList is present, attList is present, initList is present, timeList is present
        argDict.update({16 : 'query'})
        argResult = argDict[argCombo]
        
        # Other errors
        listLenErr = '-b, -a, -i elements (where specified) must all contain the same number of values'
        btsIndexOutOfRangeErr = 'BTS value(s) (-b) must be between 1 and 6'
        attIndexOutOfRangeErr = 'Attenuation value(s) (-a) must be between 1 and 93 if absolute (with -i option), or between -93 and 93 if relative (no -i option)'
        
        # Test for out of range errors
        if btsPresent and any(bts not in range(1, 7) for bts in btsList):
                raise CLIError(btsIndexOutOfRangeErr)
        if (argResult == 'absoluteRamp' or argResult == 'static') and any(att not in range(0, 94) for att in attList):
                raise CLIError(attIndexOutOfRangeErr)
        if argResult == 'relativeRamp' and any(att not in range(-93, 94) for att in attList):
                raise CLIError(attIndexOutOfRangeErr)
                    
        # Test for invalid argument combinations and list length errors
        if argResult[:26] == 'Argument Combination Error':
            raise CLIError(argResult)
        
        # Test all list arguments are the same length
        listArgs = []
        if btsPresent: listArgs.append(len(btsList))
        if attPresent: listArgs.append(len(attList))
        if initPresent: listArgs.append(len(initList))
        if timePresent: listArgs.append(len(timeList))
        if not all(x == listArgs[0] for x in listArgs):
            raise CLIError(listLenErr)
        
        # Error checking complete, now do it!
        
        # Attempt to connect..
        try:
            sock = openSock(ipAddr, port)
        except socket_error, serr:
            sys.stderr.write('''
Could not connect, can you ping the Koppelfeld? Try checking the following:
- You are physically cabled to the XPort adapter;
- You have set a correct IP address in the subnet 192.168.1.0/24 (default);
- You can ping the Koppelfeld on 192.168.1.1 (default).
          
Message:
''')
            sys.stderr.write(repr(serr) + '\n')
            return 2
        
        if argResult == 'static':
            opStatic(sock, btsList, attList)
        elif argResult == 'relativeRamp':
            opRelativeRamp(sock, btsList, attList, timeList)
        elif argResult == 'absoluteRamp':
            opAbsoluteRamp(sock, btsList, attList, initList, timeList)      
        elif argResult == 'query':
            opQuery(sock)
       
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG:
            raise e
        sys.stderr.write(program_name + ": " + str(e) + "\n\n")
        parser.print_usage(sys.stderr)
        return 2
    finally:
        if sock is not None: closeSock(sock)
    return

def opQuery(sock):
    ''' Perform a query operation. That is, query the current status of all BTS and print it to the screen '''
    result = getStat(sock)
    btsList = [1,2,3,4,5,6]
    output = ''
    for bts, value in zip(btsList, result):
        output = output + 'BTS-%d = %d (dB)\n' % (bts, value)
    print output
    return output

def opStatic(sock, btsList, attList):
    ''' Perform a static setting operation, that is a set attenuation value for one or more BTS '''
    sendCmd(sock, btsList, attList)
    return

def opRelativeRamp(sock, btsList, attList, timeList):
    ''' 
    Perform a relative ramp operation. That is where no -i option was specified.
    The initial value list needed for the ramp() method is derived by querying the status of the koppelfeld.
    The attenuation target values (specified as relative offsets where no -i option is present) are then converted
    to absolute values and put into a new list for the ramp() method call.
    '''
    initList = getStat(sock, btsList)
    attListAbsolute = []
    for init, att in zip(initList, attList):
        attListAbsolute.append(init + att)
    ramp(sock, btsList, attListAbsolute, initList, timeList)
    return

def opAbsoluteRamp(sock, btsList, attList, initList, timeList):
    ''' Perform an absolute ramp operation. That is where an -i option was specified '''
    ramp(sock, btsList, attList, initList, timeList)
    return

def openSock(ipAdd, port):
    ''' Open a TCP socket Stream using the IP address and port provided and return it '''
    mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mysock.connect((ipAdd, port))
    mysock.settimeout(5)
    return mysock

def closeSock(sock):
    ''' Close the socket '''
    sock.close()
    return
    
def sendCmd(sock, btsList, attList):
    '''
    Sets an attenuation value on the Koppelfeld using the list of one or more BTS and attenuation value pairs by
    sending a message coded in the format 'R?P?' where R? is the BTS number, and P? is the attenuation value
    '''
    for nBts, nAtt in zip(btsList, attList):
        sendMsg(sock, 'R' + str(nBts) + 'P' + str(nAtt))
    return

def getStat(sock, btsList=None):
    '''
    Sends a 'Status Check' message ('ST') command and collects the result. returns a dict with either the results for the btsList
    passed in, or all bts if no list is passed in. The order of the passed in list is preserved.
    The Koppelfeld returns the full list of attenuation values in the following format:
    'R1P?R2P?R3P?R4P?R5P?R6P?'
    Where R1 etc. refers to the BTS number, and P? refers to the set attenuation value of that BTS
    '''
    chunks = []
    chunk = ''
    result = {}
    finalResult = []
    
    # If no btsList is passed in then assume all bts status to be returned
    if btsList is None:
        btsList = [1,2,3,4,5,6]
    
    # Send the query ('ST' command)
    sendMsg(sock, 'ST')
    
    # Now collect the output until the terminating character is received ('\x03') or an error occurs
    while '\x03' not in chunk:
        try:
            chunk = sock.recv(8192)
        except socket.timeout as timeout:
            raise timeout
        if chunk == '':
            raise RuntimeError('The user has disconnected')
        chunks.append(chunk)
        
    # Join the buffer and remove the delimiters
    resultStr = ''.join(chunks)[1:-1]
    
    # Extract all attenuation values from the result string and put them in a dictionary with the bts number as key..
    allBts = [1,2,3,4,5,6]
    it = re.finditer('(?<=P)\d+', resultStr)
    for bts, match in zip(allBts,it):
        result.update({bts : int(match.group())})
    
    # now build the final result dict which will contain the att values for the btsList passed in (or all bts if none passed in)
    for bts in btsList:
        finalResult.append(result[bts])    
    
    return finalResult

def sendMsg(sock, msg):
    ''' 
    Sends msg delimited with the start and end hexadecimal bytes \x02 and \x03
    to sock which is an open client socket
    as per the protocol defined for the Koppelfeld
    returns the number of bytes sent
    '''
    pMsg = '\x02' + msg + '\x03'
    bytes_sent = sock.send(pMsg)
    return bytes_sent

def ramp(sock, btsList, attList, initList, timeList):
    '''
    Move the attenuation value of one or more BTS from it's initial value to a target value over a specified time
    The initial value, target value, and time value are set individually with all values being passed in as equal length
    lists, and each i-th element of the list being the values for one bts.
    
    The method is achieved without using threads by using a time tick loop
    '''
    # The main timing loop will sleep for TICK_DURATION on each iteration
    TICK_DURATION = 0.01
    
    # a new list of all differences between initial and target values (magnitudes only)
    diffList = []
    # a new list of either 1 or -1 depending on whether the target is more or less than the initial value
    stepSignList = []
    for init, att in zip(initList, attList):
        diffVal = float(abs(init - att))
        diffList.append(diffVal)
        stepSignList.append(-1 if att < init else 1)
        
    # The total number of ticks that the main timing loop needs to go through, calculated using the max time value of all BTS
    tickTotal = int(math.ceil(max(timeList) / TICK_DURATION))
    # The total time elapsed, updated during the running of the main timing loop
    timeElapsed = 0.0
    # a new list of the number of ticks per increment of attenuation for each BTS
    tickPerIncrementList = []
    for timeVal, diff in zip(timeList, diffList):
        tickCount = timeVal / TICK_DURATION
        tickPerIncrementList.append(math.floor(tickCount / diff))
    
    # Set all BTS to the initial value before ramping
    for bts, initVal in zip(btsList, initList):
        sendCmd(sock, [bts], [initVal])
    
    # Main timing loop
    for tick in range(1, tickTotal + 1):
        
        for bts, tickPerIncrement, stepSign, timeVal, initVal in zip(btsList, tickPerIncrementList, stepSignList, timeList, initList):
            # increment this BTS attenuation value if the current tick is a multiple of the tick per increment AND if the current
            # time elapsed is still within this BTS time value
            if tick % tickPerIncrement == 0 and timeElapsed <= timeVal:
                # if the attenuation value to send calcs as < 0 or > 93, then set to 0 or 93 respectively
                attToSend = max(min(initVal + int((tick / tickPerIncrement) * stepSign), 93), 0)
                sendCmd(sock, [bts], [attToSend])

        time.sleep(TICK_DURATION)
        timeElapsed = timeElapsed + TICK_DURATION
    return

if __name__ == "__main__":
    sys.exit(main())