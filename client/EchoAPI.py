# API to access the server
# Not exactly certain how to implement it correctly. Might get rewritten some time later

import json
import hashlib
import requests

class Exceptions:
	class EventCallException(Exception):
		pass

def _decorated_event(*args, **kwargs):
	raise EventCallException(f"Functions decorated by class.event is not supposed to be called")

class client:
	server_url = None #str
	class event:
		on_ready_function = None
		def __init__(self, owner):
			self.on_ready_function = lambda: print(owner.read_banner())
		def on_ready(self):
			def init_wrapper(function):
				self.on_ready_function = function
				return _decorated_event
	def __init__(self, server_url):
		self.server_url = server_url + ("/" if not server_url.endswith("/") else "")
		self.event = self.event(self)
	def read_banner(self):
		return requests.get(self.server_url+"banner.txt").content.decode("utf-8")
	def main_loop(self):
		self.event.on_ready_function()
	def start(self):
		self.main_loop()
