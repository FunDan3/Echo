#! /usr/bin/python3
# Library that is supposed to ease creation of http/https server
# Do not use this in any of your project. Its just a trash for school.
# HTTP is fine because server is not supposed to be able to know anything private about the user

from http.server import BaseHTTPRequestHandler, HTTPServer
import re

class Exceptions:
	class DecoratedFunctionCallException(Exception):
		pass
	class NoConditionException(Exception):
		pass
	class ConditionConflictException(Exception):
		pass

class _WebServerHandlerClass(BaseHTTPRequestHandler):
	parent = None # I am not certain should I set this or not. I think I should at least to be explicit about varaibles
	def do_GET(self):
		self.parent.on_request(self, "get")
	def do_POST(self):
		self.parent.on_request(self, "post")

class WebServer:
	get_functions_and_conditions_list = []
	post_functions_and_conditions_list = []
	handler = None #Supposed to be HTTP/HTTPS _WebServerHandlerClass
	def __init__(self, ip, port):
		self.handler = _WebServerHandlerClass
		self.handler.parent = self
		self.handler = HTTPServer((ip, port), self.handler)
		print(dir(self.handler))
		self.handler.parent = self
	def start(self):
		try:
			self.handler.serve_forever()
		except KeyboardInterrupt:
			self.handler.server_close()
	def _deco_condition_builder(self, paths):
		def check_function(WebHandler):
			return WebHandler.path in paths
		return check_function

	def get(self, paths = None, checker_function = None):
		def decorator(function):
			if not paths and not checker_function:
				raise NoConditionException(f"No conditions specified for the {function.__name__} function")
			elif paths and checker_function:
				raise ConditionConflictException(f"Two conditions conflict for the {function.__name__} function")
			def wrapped_function(*args, **kwargs):
				raise Exceptions.DecoratedFunctionCallException("Functions decorated by WebServer are not supposed to be called.")
			self.get_functions_and_conditions_list.append((function, self._deco_condition_builder(paths) if paths else checker_function))
			return wrapped_function
		return decorator

	def post(self, paths = None, checker_function = None):
		def decorator(function):
			if not paths and not checker_function:
				raise NoConditionException(f"No conditions specified for the {function.__name__} function")
			elif paths and checker_function:
				raise ConditionConflictException(f"Two conditions conflict for the {function.__name__} function")
			def wrapped_function(*args, **kwargs):
				raise Exceptions.DecoratedFunctionCallException("Functions decorated by WebServer are not supposed to be called.")
			self.post_functions_and_conditions_list.append((function, self._deco_condition_builder(paths) if paths else checker_function))
			return wrapped_function
		return decorator

	def on_request(self, handle, request_type):
		for function, condition in eval(f"self.{request_type}_functions_and_conditions_list"): #Safe in theory
			if condition(handle):
				function()
