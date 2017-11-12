WSC2
============
LAST/CURRENT VERSION: 0.1

Author: Arno0x0x - [@Arno0x0x](https://twitter.com/Arno0x0x)

WSC2 is a PoC of using the WebSockets and a browser process to serve as a C2 communication channel between an agent, running on the target system, and a controller acting as the actuel C2 server.

The tool is distributed under the terms of the [GPLv3 licence](http://www.gnu.org/copyleft/gpl.html).

Background information
----------------
Check this blog post to get some context and insight on the developpment of this tool:

[Using WebSockets and IE/Edge for C2 communications](https://arno0x0x.wordpress.com/2017/11/10/using-websockets-and-ie-edge-for-c2-communications/)

Architecture
----------------
WSC2 is composed of:
- a controller, written in Python, which acts as the C2 server
- an agent running on the target system, delivered to the target system via various initial stagers
- various flavors of initial stagers (*created from the controller interface*) used for the initial compromission of the target system

<img src="https://dl.dropboxusercontent.com/s/2znnn74iczdjbus/architecture.jpg?dl=0" width="600">

Features
----------------
WSC2 main features:
  - Various stager (*powershell one liner, various JScript file*) - this is not limited, you can easily come up with your own stagers, check the templates folder to get an idea
  - Interactive shell (*with environment persistency*)
  - File transfer back and forth between the agent and C2
  - Multiple agents support

<img src="https://dl.dropboxusercontent.com/s/ubhgex2d9h8cjr4/wsc2.jpg?dl=0" width="600">

Installation & Configuration
------------
Installation is pretty straight forward:
* Git clone this repository: `git clone https://github.com/Arno0x/WSC2 WSC2`
* cd into the WSC2 folder: `cd WSC2`
* Install the python dependencies: `pip install -r requirements.txt`
* Give the execution rights to the main script: `chmod +x wsc2.py`

Check the configuration file `config.py` and ensure the default config fits your needs.

Start the controller by typing: `./wsc2.py`.

Compiling your own agent
------------
The JScript agent (stager 'jscript1') doesn't need to be compiled.

The 'jscript2', 'jscript3' and 'psoneliner' stagers are based on a .Net assembly DLL that you can choose to build on your own/modify, based on the source code provided.

Although it is perfectly OK to use the provided *wsc2.dll*, you can very easily compile your own agent, from the source code provided. You'll need Visual Studio installed.

Create a .Net (Visual C#) Class Libray projet. Add the wsc2Agent.cs source file as the main source code file.

Add the following references to your project:
  1. Microsoft HTML Object Library (MSHTML)
  2. Microsoft Internet Controls (SHDocVw)

Build !

Todo
----------------
  - Add end-to-end encryption layer to communications
  - Add support for more agent features (*run PS module, take screenshots, keylogger, etc.*)

DISCLAIMER
----------------
This tool is intended to be used in a legal and legitimate way only:
  - either on your own systems as a means of learning, of demonstrating what can be done and how, or testing your defense and detection mechanisms
  - on systems you've been officially and legitimately entitled to perform some security assessments (pentest, security audits)

Quoting Empire's authors:
*There is no way to build offensive tools useful to the legitimate infosec industry while simultaneously preventing malicious actors from abusing them.*

CREDITS
------------

- [@HackingDave](https://twitter.com/HackingDave) for inspiring me based on his TrevorC2 project

- [@tiraniddo](https://twitter.com/tiraniddo) for the amazing DotNetToJScript project.