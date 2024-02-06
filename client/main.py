#! /usr/bin/python3
#I am rushing to finish this project because It needs to be done week before I started writing this file

import EchoAPI
import SymetricEncryptionLayer as SEL

import random
import pickle
import os
import asyncio
import hashlib
import aioconsole

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

async def console_prompt():
	help_message = """
help - see this menu
exit - exit messager
read <optional: quantity> - read <quantity> messages. if quantity isnt specified then all messages will be displayed
profile <positional: username> - display username and publick hash of the user.
message <positional: username> - start typing message to <username>. You should check recipient public hash using profile command to validate their identity.
"""
	user_input = await aioconsole.ainput(f"{client.user.username}:{client.user.public_hash} > ")
	arguments = user_input.split(" ")
	command = arguments[0]; arguments.pop(0)
	if command not in "help;exit;read;profile;message".split(";"):
		print(f"Unknown command '{command}'")
		return
	if command == "help":
		if arguments:
			print("Command 'help' doesnt take any arguments")
			return
		print(help_message)
	if command == "exit":
		if arguments:
			print("Command 'exit' doesnt take any arguments")
			return
		raise KeyboardInterrupt("Program finished")

@client.event.on_ready()
async def on_ready():
	print("You are connected. Developer of this messager is a failure at GUIs so currently only console is supported\nTo see help type 'help'")
	while True:
		print(f"You have {len(messages)} unread messages.")
		await console_prompt()

@client.event.on_message()
async def on_message(message):
	global messages
	messages.append(message)
	write_message_file(client.password, messages)

client.start()
