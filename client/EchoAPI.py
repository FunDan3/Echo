# API to access the server
# Not exactly certain how to implement it correctly. Might get rewritten some time later

import json
import hashlib
import requests
import pickle
import PQCryptoLayer as crypto
import copy
class Exceptions:
	class EventCallException(Exception):
		pass
	class InvalidRequestException(Exception):
		pass
	class DeceptiveServerException(Exception):
		pass

def _decorated_event(*args, **kwargs):
	raise EventCallException(f"Functions decorated by class.event is not supposed to be called")

def bytes_to_numbers(key):
        return [int(byte) for byte in key]

class user_obj:
	parent = None #set in client class
	username = None
	public_key = None
	public_sign = None
	def __init__(self, username):
		self.username = username
		self.public_key = self.parent.basic_request_get("public_key", json_data = {"username": username}).content
		self.public_sign = self.parent.basic_request_get("public_sign", json_data = {"username": username}).content

class client:
	server_url = None #str
	token = None #str
	username = None #str
	public_key = None #bytes
	private_key = None #bytes
	public_sign = None #bytes
	private_sign = None #bytes
	user = None
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
		self.user_obj = copy.deepcopy(user_obj) #I have no idea how to implement it better
		self.user_obj.parent = self

	def verify_response(self, response):
		if response.status_code not in range(200, 300):
			raise Exceptions.InvalidRequestException(response.content.decode("utf-8"))

	def basic_request_post(self, path, json_data = None, data = None):
		if not json_data:
			json_data = {}
		if not data:
			data = b""
		to_send = json.dumps(json_data).encode("utf-8") + b"\n" + data
		response = requests.post(self.server_url + path, data = to_send)
		self.verify_response(response)
		return response

	def auth_request_post(self, path, json_data = None, data = None):
		if not json_data:
			json_data = {}
		json_data["login"] = self.user.username
		json_data["token"] = self.token
		return self.basic_request_post(path, json_data, data)

	def basic_request_get(self, path, json_data = None):
		if not json_data:
			json_data = {}
		first = True
		for key, value in json_data.items():
			path += ("?" if first else "&") + f"{key}={value}"
			first = False
		response = requests.get(self.server_url + path)
		self.verify_response(response)
		return response

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
		public_key, self.private_key, public_sign, self.private_sign = cryptodata
		self.token = self.basic_request_post("register", json_data = {"login": username,
			"password": password,
			"public_key": bytes_to_numbers(public_key),
			"public_sign": bytes_to_numbers(public_sign)}).content.decode("utf-8")
		self.user = self.user_obj(username)
		return self.generate_container()

	def generate_container(self):
		data = {"username": self.user.username,
			"token": self.token,
			"public_key": self.user.public_key,
			"private_key": self.private_key,
			"public_sign": self.user.public_sign,
			"private_sign": self.private_sign}
		return pickle.dumps(data)

	def login(self, container):
		data = pickle.loads(container) #not quite safest but should be trusted
		self.user = self.user_obj(data["username"])

		public_key = data["public_key"]
		public_sign = data["public_sign"]
		if public_key != self.user.public_key or public_sign != self.user.public_sign:
			raise Exceptions.DeceptiveServerException("Server's response to public key/sign doesnt match recorded one")

		self.token = data["token"]
		self.private_key = data["private_key"]
		self.private_sign = data["private_sign"]
		login_request = self.auth_request_post("login")

	def read_banner(self):
		return self.basic_request_get("banner.txt").content.decode("utf-8")

	def main_loop(self):
		self.event.on_ready_function()

	def start(self):
		self.main_loop()
