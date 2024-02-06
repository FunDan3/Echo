#! /usr/bin/python3

import EchoAPI
import pickle
import os

client = EchoAPI.client("http://127.0.0.1:8080")
print(client.read_banner())
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
				with open("./container.epickle", "rb") as container_file:
					client.login(container_file.read(), input("Password: "))
					break
			except ValueError:
				print("Password is invalid. Try again.")

@client.event.on_ready()
async def on_ready():
	return

login_prompt()
client.start()
