#! /usr/bin/python3

import EchoAPI
import SymetricEncryptionLayer as SEL

import random
import pickle
import os
import asyncio
import hashlib

def hash(data, algorithm = None):
	if not algorithm:
		algorithm = "sha256"
	if type(data)!=bytes:
		data = data.encode("utf-8")
	data_hash = hashlib.new(algorithm)
	data_hash.update(data)
	return data_hash.digest()

def login_prompt():
	if not os.path.exists("./container.epickle"):
		print("Container not found. Starting registration process")
		while True:
			try:
				nickname = input("Nickname: ")
				password = input("Password: ")
				if not os.path.exists("./cryptodata.pickle"):
					print("No cryptodata file found. Generating random one...")
					container = client.register(nickname, password)
				else:
					print("Cryptodata file found. Importing...")
					with open("./cryptodata.pickle", "rb") as cryptodata_file:
						container = client.register(nickname, password, cryptodata = pickle.loads(cryptodata_file.read()))
				with open("./container.epickle", "wb") as container_file:
					container_file.write(container)
					break
			except EchoAPI.Exceptions.InvalidRequestException as e:
				print(f"{e}, try again")
	else:
		print("Container found. Enter password to decrypt it")
		while True:
			try:
				password = input("Password: ")
				with open("./container.epickle", "rb") as container_file:
					client.login(container_file.read(), password)
					break
			except ValueError:
				print("Password is invalid. Try again.")

def read_message_file(password):
	if not os.path.exists("./messages.epickle"):
		write_message_file(password, [])
		return []
	else:
		with open("./messages.epickle", "rb") as message_file:
			return pickle.loads(SEL.decrypt(hash(password), message_file.read()))

def write_message_file(password, messages_list):
	while True:
		try:
			with open("./messages.epickle", "wb") as message_file:
				message_file.write(SEL.encrypt(hash(password), pickle.dumps(messages_list)))
			break
		except KeyboardInterrupt as e:
			print("Saving message file. Please wait")
			raise e
client = EchoAPI.client("http://127.0.0.1:8080")
print(client.read_banner())
login_prompt()
messages = read_message_file(client.password)

@client.event.on_ready()
async def on_ready():
	return

@client.event.on_message()
async def on_message(message):
	global messages
	messages.append(message)
	write_message_file(client.password, messages)

client.start()
