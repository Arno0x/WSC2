# -*- coding: utf8 -*-
"""

Miscelaneous helper functions used in WSC2

"""

import shlex
from subprocess import Popen, PIPE
import string
import base64
from string import Template
from Crypto.Random import random

import config

#------------------------------------------------------------------------
def cloneSite(userAgent, url):
	# Download remote site page
	proc = Popen("wget --no-check-certificate -q -O /tmp/index.html -c -k -U \"{0}\" \"{1}\"".format(userAgent, url), stderr=PIPE, shell=True).wait()
	if proc == 0:
		proc = Popen("cat /tmp/index.html", shell=True, stdout=PIPE)
		result = ''
		for line in proc.stdout:
			result = result + line
		return result
	else:
		print color("[!] Error executing wget")
		return None

#------------------------------------------------------------------------
def b64encode(data):
	return base64.b64encode(data)

def b64decode(data):
	return base64.b64decode(data)

#------------------------------------------------------------------------
def chunks(s, n):
	"""
	Author: HarmJ0y, borrowed from Empire
	Generator to split a string s into chunks of size n.
	"""
	for i in xrange(0, len(s), n):
		yield s[i:i+n]

#------------------------------------------------------------------------
def powershellEncode(rawData):
	"""
	Author: HarmJ0y, borrowed from Empire
	Encode a PowerShell command into a form usable by powershell.exe -enc ...
	"""
	return base64.b64encode("".join([char + "\x00" for char in unicode(rawData)]))

#------------------------------------------------------------------------
def convertFromTemplate(parameters, templateFile):
	try:
		with open(templateFile) as f:
			src = Template(f.read())
			result = src.substitute(parameters)
			f.close()
			return result
	except IOError:
		print color("[!] Could not open or read template file [{}]".format(templateFile))
		return None

#------------------------------------------------------------------------
def randomString(length = -1, charset = string.ascii_letters):
    """
    Author: HarmJ0y, borrowed from Empire
    Returns a random string of "length" characters.
    If no length is specified, resulting string is in between 6 and 15 characters.
    A character set can be specified, defaulting to just alpha letters.
    """
    if length == -1: length = random.randrange(6,16)
    random_string = ''.join(random.choice(charset) for x in range(length))
    return random_string

#------------------------------------------------------------------------
def randomInt(minimum, maximum):
	""" Returns a random integer between or equald to minimum and maximum
	"""
	if minimum < 0: minimum = 0
	if maximum < 0: maximum = 100
	return random.randint(minimum, maximum)

#------------------------------------------------------------------------
def retrieveQuotedArgs(args, maxNbArgs):
	"""Parses arguments that may contain double quote for escaping spaces in arguments"""
	nbArgs = 0
	result = []

	# Remove trailing and starting spaces
	args = args.strip()

	temp = shlex.split(args)
	if len(temp) <= maxNbArgs:
		return temp
	else:
		result = temp[:maxNbArgs-1]
		result.append(' '.join(temp[maxNbArgs-1:len(temp)]))
		return result

#------------------------------------------------------------------------
def color(string, color=None, bold=None):
    """
    Author: HarmJ0y, borrowed from Empire
    Change text color for the Linux terminal.
    """
    
    attr = []
    
    if color:
    	if bold:
    		attr.append('1')
        if color.lower() == "red":
            attr.append('31')
        elif color.lower() == "green":
            attr.append('32')
        elif color.lower() == "blue":
            attr.append('34')

        return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)
    else:
		if string.strip().startswith("[!]"):
			attr.append('1')
			attr.append('31')
			return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)
		elif string.strip().startswith("[+]"):
			attr.append('1')
			attr.append('32')
			return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)
		elif string.strip().startswith("[?]"):
			attr.append('1')
			attr.append('33')
			return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)
		elif string.strip().startswith("[*]"):
			attr.append('1')
			attr.append('34')
			return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)
		else:
			return string

#------------------------------------------------------------------------
def printBanner():
	print color("""
	
██╗    ██╗███████╗ ██████╗██████╗ 
██║    ██║██╔════╝██╔════╝╚════██╗
██║ █╗ ██║███████╗██║      █████╔╝
██║███╗██║╚════██║██║     ██╔═══╝ 
╚███╔███╔╝███████║╚██████╗███████╗
 ╚══╝╚══╝ ╚══════╝ ╚═════╝╚══════╝
                                  
	""", "blue")

