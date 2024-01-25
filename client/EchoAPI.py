# API to access the server
# Not exactly certain how to implement it correctly. Might get rewritten some time later

import json
import hashlib
import requests
import pickle
import PQCryptoLayer as crypto
class Exceptions:
	class EventCallException(Exception):
		pass

def _decorated_event(*args, **kwargs):
	raise EventCallException(f"Functions decorated by class.event is not supposed to be called")

def bytes_to_numbers(key):
        return [int(byte) for byte in key]

class client:
	server_url = None #str
	token = None #str
	username = None #str
	public_key = None #bytes
	private_key = None #bytes
	public_sign = None #bytes
	private_sign = None #bytes
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
	def generate_keys(self, condition):
		while True:
			public_key, private_key = crypto.encryption.generate_keypair()
			if condition(public_key, private_key):
				return public_key, private_key
	def generate_signs(self, condition):
		while True:
			public_sign, private_sign = crypto.signing.generate_signs()
			if condition(public_sign, private_sign):
				return public_sign, private_sign
	def generate_cryptodata(self, key_condition = None, sign_condition = None, overall_condition = None):
		anything = lambda *args, **kwargs: True
		if not key_condition:
			key_condition = anything
		if not sign_condition:
			sign_condition = anything
		if not overall_condition:
			overall_condition = anything
		while True:
			public_key, private_key = self.generate_keys(key_condition)
			public_sign, private_sign = self.generate_signs(sign_condition)
			if overall_condition(public_key, private_key, public_sign, private_sign):
				return public_key, private_key, public_sign, private_sign
	def register(self, username, password, cryptodata = None):
		if not cryptodata:
			cryptodata = self.generate_cryptodata()
		self.public_key, self.private_key, self.public_sign, self.private_sign = cryptodata
		self.token = requests.post(self.server_url+"register", json = {"login": username,
			"password": password,
			"public_key": bytes_to_numbers(self.public_key),
			"public_sign": bytes_to_numbers(self.public_sign)}).content.decode("utf-8")
		self.username = username
		return self.generate_container()
	def generate_container(self):
		data = {"username": self.username,
			"token": self.token,
			"public_key": self.public_key,
			"private_key": self.private_key,
			"public_sign": self.public_sign,
			"private_sign": self.private_sign}
		return pickle.dumps(data)
	def login(self, container):
		data = pickle.loads(container) #not quite safest but should be trusted
		for varaible, value in data.items():
			setattr(self, varaible, value)
		login_request = requests.post(self.server_url+"login", json = {"login": self.username, "token": self.token})
		if login_request.status_code!=200:
			raise Exception(login_request.content.decode("utf-8"))
	def read_banner(self):
		return requests.get(self.server_url+"banner.txt").content.decode("utf-8")
	def main_loop(self):
		self.event.on_ready_function()
	def start(self):
		self.main_loop()
