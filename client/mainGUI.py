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
	else:
		layout = [[sg.Text("Registration")],
			  [sg.Text("Login:", size=(10,1)), sg.Input(key = "-LOGIN-")],
			  [sg.Text("Password:", size=(10,1)), sg.Input(key = "-PASSWORD-")],
			  [sg.Text(key = "-OUTPUT-")],
			  [sg.Button("Register")]]
		window = sg.Window("Registration", layout)
		while True:
			event, values = window.read()
			if event == sg.WINDOW_CLOSED:
				raise KeyboardInterrupt("Program finished")
			if event == "Register":
				try:
					if os.path.exists("./cryptodata.pickle"):
						with open("./cryptodata.pickle", "rb") as cryptodata_file:
							client.register(values["-LOGIN-"], values["-PASSWORD-"], pickle.loads(cryptodata_file.read()))
							break
					else:
						client.register(values["-LOGIN-"], values["-PASSWORD-"])
						break
				except Exception as e:
					window["-OUTPUT-"].update(str(e))
		window.close()
		with open("./container.epickle", "wb") as container_file:
			container_file.write(client.generate_container())
def login_prompt():
	banner_window()
	login_window()

async def main_window():
	previous_user_name = None
	message_tab = [[sg.Text("User:", size = (10, 1)), sg.Input(key = "-USER-")],
		       [sg.Text("", key = "-PUBLIC_HASH-")],
		       [sg.Multiline(key = "-MESSAGE-", size = (70, 10))],
		       [sg.Button("Send")]]
	layout = [[sg.TabGroup([[sg.Tab("Send message", message_tab)]])]]
	window = sg.Window("Echo messager", layout)
	window.NonBlocking = True
	while True:
		event, values = window.read(timeout = 0)
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		if values["-USER-"] != previous_user_name:
			previous_user_name = values["-USER-"]
			try:
				user = EchoAPI.User(values["-USER-"])
				window["-PUBLIC_HASH-"].update(user.public_hash)
			except Exception as e:
				window["-PUBLIC_HASH-"].update(str(e))
		await asyncio.sleep(1/30)
		if event == "Send":
			try:
				user = EchoAPI.User(values["-USER-"])
				user.dm_text(values["-MESSAGE-"])
				window["-MESSAGE-"].update("")
				window["-USER-"].update("")
				window["-PUBLIC_HASH-"].update("Message have been sent")
				previous_user_name = ""
			except Exception as e:
				pass
	window.close()

login_prompt()
#messages = read_message_file(client.password)

@client.event.on_ready()
async def on_ready():
	await main_window()

client.start()
