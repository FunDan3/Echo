# API to access the server
# Not exactly certain how to implement it correctly. Might get rewritten some time later

import json
import hashlib
import requests
import pickle
import PQCryptoLayer as crypto
import SymetricEncryptionLayer as SEL
import copy
import asyncio
import base64

class Exceptions:
	class EventCallException(Exception):
		pass
	class InvalidRequestException(Exception):
		pass
	class DeceptiveServerException(Exception):
		pass
	class MultipleClientsLaunchedException(Exception):
		pass
def _decorated_event(*args, **kwargs):
	raise EventCallException(f"Functions decorated by class.event is not supposed to be called")

def bytes_to_numbers(key):
        return [int(byte) for byte in key]

class _folder:
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

class Message:
	sent_time = None
	author = None
	content = None
	parent = None
	type = None
	metadata = None
	def __init__(self, server_response_content):
		json_data = json.loads(server_response_content.split(b"\n", 1)[0])
		message_data = server_response_content.split(b"\n", 1)[1]
		self.sent_time = json_data["time"]
		self.author = User(json_data["Sender"])
		self.retrieve_content(self._decrypt_message(message_data))

	def retrieve_content(self, data):
		json_data = json.loads(data.split(b"\n", 1)[0])
		self.content = data.split(b"\n", 1)[1]
		self.metadata = _folder(**json_data["metadata"])
		split_type = json_data["type"].split("#", 1) #format for json_data['type']: {primary type}/{secondary type}#{encoding (optional)}
		self.type = split_type[0]
		if len(split_type) == 2: #if encoding is specified
			encoding = split_type[1]
			self.content = self.content.decode(encoding)
		if json_data["public_hash"] != self.author.public_hash:
			raise DeceptiveServerException(f"Server tried to spoof public key / sign of {message.author.username}")

	def _decrypt_message(self, encrypted_message):
		unverified_message = crypto.encryption.decrypt(self.parent.private_key, encrypted_message)
		verified_message = crypto.signing.verify(self.author.public_sign, unverified_message)
		return verified_message

class User:
	parent = None #set in client class
	username = None
	public_key = None
	public_sign = None
	public_hash = None
	def __init__(self, username):
		self.username = username
		self.public_key = self.parent.basic_request_get("public_key", json_data = {"username": username}).content
		self.public_sign = self.parent.basic_request_get("public_sign", json_data = {"username": username}).content
		public_hash = hashlib.new("md5")
		public_hash.update(self.public_key)
		public_hash.update(self.public_sign)
		self.public_hash = base64.b64encode(public_hash.digest()).decode("utf-8").replace("=", "")

	def dm_raw_bytes(self, raw_data):
		to_send = crypto.encryption.encrypt(self.public_key, crypto.signing.sign(self.parent.private_sign, raw_data))
		self.parent.auth_request_post("message", json_data = {"recipient": self.username}, data = to_send)

	def dm_text(self, text, encoding = None, metadata = None):
		if not metadata:
			metadata = {}
		if not encoding:
			encoding = "utf-8"
		if type(text)!=str:
			raise TypeError(f"text type should be string. Got: {type(text)}")
		json_data = json.dumps({"type": f"text/plain#{encoding}", "metadata": metadata, "public_hash": self.parent.user.public_hash})
		to_send = json_data.encode("utf-8") + b"\n" + text.encode(encoding)
		self.dm_raw_bytes(to_send)

class client:
	server_url = None #str
	username = None #str
	main_loop_delay = None #int/float
	private_key = None #bytes
	private_sign = None #bytes
	password = None #string
	user = None
	class event:
		on_ready_function = None
		on_message_function = None
		def __init__(self, owner):
			async def on_ready_function():
				print(owner.read_banner())
			async def on_message_function(message):
				print(f"{message.author.username}:{message.author.public_hash} -> {message.content}")
			self.on_ready_function = on_ready_function
			self.on_message_function = on_message_function

		def on_ready(self):
			def init_wrapper(function):
				self.on_ready_function = function
				return _decorated_event
			return init_wrapper

		def on_message(self):
			def init_wrapper(function):
				self.on_message_function = function
				return _decorated_event
			return init_wrapper

	def __init__(self, server_url, main_loop_delay = 10):
		self.server_url = server_url + ("/" if not server_url.endswith("/") else "")
		self.event = self.event(self)
		if User.parent:
			raise Exceptions.MultipleClientsLaunchedException("You can not run multiple clients at the same time")
		User.parent = self
		Message.parent = self
		self.main_loop_delay = main_loop_delay

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
		json_data["password"] = self.password
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
		self.password = password
		self.basic_request_post("register", json_data = {"login": username,
			"password": password,
			"public_key": bytes_to_numbers(public_key),
			"public_sign": bytes_to_numbers(public_sign)}).content.decode("utf-8")
		self.user = User(username)
		return self.generate_container()

	def fetch_message(self):
		server_response = self.auth_request_post("fetch_message").content
		if not server_response:
			return None
		return Message(server_response)

	def fetch_messages(self):
		collected_messages = []
		while True:
			message = self.fetch_message()
			if not message:
				break
			collected_messages.append(message)
		return collected_messages

	def generate_container(self):
		data = {"username": self.user.username,
			"password": self.password,
			"public_key": self.user.public_key,
			"private_key": self.private_key,
			"public_sign": self.user.public_sign,
			"private_sign": self.private_sign}
		password_hash = hashlib.new("sha-256")
		password_hash.update(self.password.encode("utf-8"))
		return SEL.encrypt(password_hash.digest(), pickle.dumps(data))

	def login(self, container, password):
		password_hash = hashlib.new("sha-256")
		password_hash.update(password.encode("utf-8"))

		data = pickle.loads(SEL.decrypt(password_hash.digest(), container))
		self.user = User(data["username"])

		public_key = data["public_key"]
		public_sign = data["public_sign"]
		if public_key != self.user.public_key or public_sign != self.user.public_sign:
			raise Exceptions.DeceptiveServerException("Server's response to public key/sign doesnt match recorded one")

		self.password = data["password"]
		self.private_key = data["private_key"]
		self.private_sign = data["private_sign"]
		login_request = self.auth_request_post("login")

	def read_banner(self):
		return self.basic_request_get("banner.txt").content.decode("utf-8")

	async def message_loop(self):
		while True:
			for message in self.fetch_messages():
				await self.event.on_message_function(message)
			await asyncio.sleep(self.main_loop_delay)

	async def async_start(self):
		await asyncio.gather(self.event.on_ready_function(), self.message_loop())

	def start(self):
		asyncio.run(self.async_start())
