<h1>mts-attenuator-controller</h1>
<hr>
A script to control the MTS System Technik SCF-0300 Digital Variable Attenuator (http://www.mts-systemtechnik.de/index.php/mts_en/Products/Devices-Systems/Standard-Coupling-Units/SCF-0300-SCF-0301-LAN-Standard-Coupling-Field). The script allows the dynamic ramping up and down of attenuation values on all channels independently and simultaneously, which enables the the user to perform simulations of movement through radio environments

The MTS System Technik Digital Variable Attenuator is a 6-channel (hereafter called 'BTS') digitally controlled variable attenuator that can set RF sttenuation values of betweenm 0 and 93 dB for channels from 400MHz to 2900MHz.
The LAN version of the attenuato comes fitted with an 'X-Port' Serial-over-LAN interface, which implements the simple serial protocol over TCP sockets. This allows control of the attenuator via a standard IP network.

<h2>FUNCTIONAL OVERVIEW:</h2>
<hr>
The script is able to perform concurrent operations on multiple BTS. Each argument (excluding -q -m and -h) accepts a list of numbers, 
separated by spaces.
The i-th element of each list refers to the parameters for the operation to be performed on the i-th BTS. To illustrate: 
<h3>Parameters passed:</h3>
<hr>
-b 1 2 3
-a -10 10 20
-t 5 30 10
As -b -a and -t are specified this is a relative ramping operation (see below). The following operations will be completed as a result:
<h3>Operations completed:</h3>
<ul>
<li>BTS 1 attenuation value will be reduced by 10 over 5 seconds</li>
<li>BTS 2 attenuation value will be increased by 10 over 30 seconds</li>
<li>BTS 3 attenuation value will be increased by 20 over 10 seconds</li>
</ul>
Each of these operations will run concurrently. That is: they will all start at the same time (although they may not finish at the same time, depending on the values set in the -t option).
The mention of a 'relative ramping operation' in the previous paragraph now requires some explanation.
The script accepts 5 primary arguments and the presence, or not, of these arguments determines the operation requested. Briefly, these operations are described as follows:
<ul>
<li>-q option only - Query only, prints the current value of the attenuation set and exits;</li>
<li>-b -a options only - Static operation, sets the attenuation values of the BTS' specified;</li>
<li>-b -a -t options only - Relative ramping operation, moves the attenuation values of the BTS' specified in the -b option by the relative offsets specified in the -a option over the times specified in the -t option;</li>
<li>-b -a -t -i options - Absolute ramping operation, moves the attenuation values of the BTS' specified in the -b option from the initial values specified in the -i option, the obsolute target values specified in the -a option over the times specified in the -t option.</li>
</ul>
In a ramping operation, the attenuation value is incremented by one at each time step. The duration of a time step is determined by the total operation time and the difference between initial and target values. All this is calculated automatically by the script leaving the user to only have to specify the parameters as described above.

<h2>STUB SERVER:</h2>
<hr>
A stub server is included in the 'server' folder, which allows users to test the script without having a physical MTS attenuator present.
In order to use the server, simply start the server CLI and it will show it's status in a command window while it waits for commands. To stop it just hit Ctrl+C.
Once the server is running, the main script may be tested by pointing it to port 4001 on the localhost, e.g:

kcv2.py -d 127.0.0.1 -p 4001 etc. etc..

Happy testing!
