# -*- coding: utf8 -*-
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop

from threading import Thread
import logging

import config

#****************************************************************************************
# Command line interactions thread
#****************************************************************************************
class WebSocketHandler(tornado.websocket.WebSocketHandler):
	def __init__(self, *args, **kwargs):
		self.agentQueue = kwargs.pop('queue')
		super(WebSocketHandler, self).__init__(*args, **kwargs)
	
	def open(self):
		address = self.request.connection.context.address
		ID = address[0]+':'+str(address[1])		
		self.agentQueue.put({'type':'open', 'ID': ID, 'wsHandler': self})
 
	def on_message(self, message):
		self.agentQueue.put({'type':'response', 'value': message})

	def on_close(self):
		address = self.request.connection.context.address
		ID = address[0]+':'+str(address[1])
		self.agentQueue.put({'type':'close', 'ID': ID})
 
#****************************************************************************************
# Command line interactions thread
#****************************************************************************************
class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
 
#****************************************************************************************
# Command line interactions thread
#****************************************************************************************
class Application(tornado.web.Application):
    def __init__(self, queue):

        handlers = [
            #(r'/', IndexPageHandler),
            (r'/ws', WebSocketHandler, {'queue': queue}),
            (r'/(.*)', tornado.web.StaticFileHandler, {'path': config.STATICFILES})
        ]
 
        settings = {
        	'debug': False,
            'template_path': './html'
        }
        tornado.web.Application.__init__(self, handlers, **settings)

#****************************************************************************************
# Thread holding Tornado Websocket server
#****************************************************************************************
class WebSocketServerThread(Thread):
	#------------------------------------------------------------------------
	# Constructor
	def __init__(self, agentQueue):
		Thread.__init__(self)
		self.agentQueue = agentQueue

	#------------------------------------------------------------------------
	# Thread entry point
	def run(self):
		logging.getLogger('tornado.access').disabled = True # Disabling Tornado local logging
		ws_app = Application(self.agentQueue)
		server = tornado.httpserver.HTTPServer(ws_app)
		server.listen(config.PORT)
		
		tornado.ioloop.IOLoop.instance().start()
