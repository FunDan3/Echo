#! /usr/bin/python3

import EchoAPI
import SymetricEncryptionLayer as SEL

import PySimpleGUI as sg
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

def banner_window():
	sg.theme("DarkAmber")
	layout = [[sg.Text(client.read_banner())],
		  [sg.Button("Ok")]]
	window = sg.Window("Banner", layout)
	while True:
		event, values = window.read()
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		if event == "Ok":
			break
	window.close()

def login_window():
	sg.theme("DarkAmber")
	if os.path.exists("./container.epickle"):
		layout = [[sg.Text("Container found. Please enter password to decrypt it")],
			  [sg.Input(key = "-PASSWORD-")],
			  [sg.Text(key = "-OUTPUT-")],
			  [sg.Button("Ok")]]
		window = sg.Window("Login", layout)
		while True:
			event, values = window.read()
			if event == sg.WINDOW_CLOSED:
				raise KeyboardInterrupt("Program finished")
			if event == "Ok":
				with open("./container.epickle", "rb") as container_file:
					try:
						client.login(container_file.read(), values["-PASSWORD-"])
						break
					except Exception as e:
						window["-OUTPUT-"].update(str(e))
		window.close()
def login_prompt():
	banner_window()
	login_window()

login_prompt()
#messages = read_message_file(client.password)

@client.event.on_ready()
async def on_ready():
	pass

@client.event.on_message()
async def on_message(message):
	pass

client.start()
