#! /usr/bin/python3

import EchoAPI
import os

client = EchoAPI.client("http://127.0.0.1:8080")

def login_prompt():
	if not os.path.exists("./container.epickle"):
		print("Container not found. Starting registration process")
		while True:
			try:
				nickname = input("Nickname: ")
				password = input("Password: ")
				client.register(nickname, password)
				with open("./container.epickle", "wb") as container_file:
					container_file.write(client.generate_container())
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

login_prompt()
client.start()
