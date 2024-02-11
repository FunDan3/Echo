#! /usr/bin/python3

import EchoAPI
import SymetricEncryptionLayer as SEL

import PySimpleGUI as sg
import pickle
import os
import asyncio
import hashlib
import aiohttp
import time
import json

program_version = "0.0.1"
program_flavour = "vanilla"

settings = None

def read_settings():
	global settings
	try:
		with open("./settings.json", "rb") as f:
			settings = json.loads(f.read())
	except Exception:
		print("Settings file is corrupted or doesnt exist. Resetting them")
		settings = {"DefaultConnect": "", "DontShowBannersOn": []}
		write_settings()

def write_settings(): #settings are probably not worth encrypting
	with open("./settings.json", "wb") as f:
		f.write(json.dumps(settings).encode("utf-8"))

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

async def banner_window(client):
	global settings
	if client.server_url in settings["DontShowBannersOn"]:
		return
	sg.theme("DarkAmber")
	layout = [[sg.Text(await client.read_banner())],
		  [sg.Button("Ok"), sg.Checkbox("Dont show banner from this server ever again", default = False, key = "-DONT_SHOW-")]]
	window = sg.Window("Banner", layout)
	while True:
		event, values = window.read()
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		if event == "Ok":
			if values["-DONT_SHOW-"]:
				settings["DontShowBannersOn"].append(client.server_url)
				write_settings()
			break
	window.close()

async def login_window(client):
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
						await client.login(container_file.read(), values["-PASSWORD-"])
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
							await client.register(values["-LOGIN-"], values["-PASSWORD-"], pickle.loads(cryptodata_file.read()))
							break
					else:
						await client.register(values["-LOGIN-"], values["-PASSWORD-"])
						break
				except Exception as e:
					window["-OUTPUT-"].update(str(e))
		window.close()
		with open("./container.epickle", "wb") as container_file:
			container_file.write(client.generate_container())

async def login_prompt(client):
	await banner_window(client)
	await login_window(client)

async def main_window():
	previous_user_name = " "
	message_tab = [[sg.Text("User:", size = (10, 1)), sg.Input(key = "-USER-")],
		       [sg.Text("", key = "-PUBLIC_HASH-")],
		       [sg.Text("", key = "-KEM_ALGO-")],
		       [sg.Text("", key = "-SIG_ALGO-")],
		       [sg.Multiline(key = "-MESSAGE-", size = (70, 10))],
		       [sg.Button("Send", key = "-SEND-", visible = False)]]
	inbox_tab = [[sg.Text("", size = (70, 20), key = "-INBOX-")]]
	layout = [[sg.TabGroup([[sg.Tab("Send message", message_tab), sg.Tab("Inbox", inbox_tab)]])]]
	window = sg.Window("Echo messager", layout)
	window.NonBlocking = True
	while True:
		event, values = window.read(timeout = 0)
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		window["-INBOX-"].update(inbox_value)
		if values["-USER-"] != previous_user_name:
			previous_user_name = values["-USER-"]
			try:
				user = EchoAPI.User(values["-USER-"])
				await user.load()
				window["-PUBLIC_HASH-"].update(user.public_hash)
				window["-KEM_ALGO-"].update(user.kem_algorithm, visible = True)
				window["-SIG_ALGO-"].update(user.sig_algorithm, visible = True)
				window["-SEND-"].update(visible = True)
			except Exception as e:
				window["-SEND-"].update(visible = False)
				window["-KEM_ALGO-"].update(visible = False)
				window["-SIG_ALGO-"].update(visible = False)
				window["-PUBLIC_HASH-"].update(str(e))
		if event == "-SEND-":
			user = EchoAPI.User(values["-USER-"])
			await user.load()
			await user.dm_text(values["-MESSAGE-"])
			window["-MESSAGE-"].update("")
			window["-USER-"].update("")
			window["-PUBLIC_HASH-"].update("Message have been sent")
			window["-SEND-"].update(visible = False)
			window["-KEM_ALGO-"].update(visible = False)
			window["-SIG_ALGO-"].update(visible = False)

			previous_user_name = ""
		await asyncio.sleep(1/30)
	window.close()

async def connect_window():
	global settings
	sg.theme("DarkAmber")
	if settings["DefaultConnect"]:
		return settings["DefaultConnect"]
	layout = [[sg.Text("Please choose the server to connect to. If you are uncertain leave default one")],
		  [sg.Input("foxomet.ru", key = "-SERVER_ADDRESS-")],
		  [sg.Text(key = "-OUTPUT-")],
		  [sg.Button("Connect", key = "-CONNECT_BUTTON-", visible = False), sg.Checkbox("Connect to this server automatically", default = True, key = "-AUTOCONNECT-")]]
	window = sg.Window("Connect", layout)
	previous_server = ""
	while True:
		event, values = window.read(timeout = 0)
		time_started = time.time()
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		try:
			server = f"https://{values['-SERVER_ADDRESS-']}:22389/"
			if server != previous_server and values["-SERVER_ADDRESS-"]:
				previous_server = server
				async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(0.5)) as session:
					async with session.get(server+"echo-messager-server-info") as response:
						server_status = response.status
						server_response = await response.read()
				if server_status != 200:
					raise Exception(f"Server returned http status code {server_response.status_code}")
				server_data = json.loads(server_response)
				window["-OUTPUT-"].update("Server detected")
				if server_data["flavour"] != program_flavour:
					raise Exception(f"Server has {server_data['flavour']} which doesnt match with client flavour ({program_flavour})")
				if server_data["version"] != program_version:
					window["-OUTPUT-"].update(f"Server version is {server_data['version']} but client version is {program_version}")
					window["-CONNECT_BUTTON-"].update("Connect anyways", visible = True)
					window["-AUTOCONNECT-"].update(visible = True)
				else:
					window["-OUTPUT-"].update(f"Server is 100% comatible")
					window["-CONNECT_BUTTON-"].update("Connect", visible = True)
					window["-AUTOCONNECT-"].update(visible = True)
		except Exception as e:
			window["-OUTPUT-"].update(str(e))
			window["-CONNECT_BUTTON-"].update(visible = False)
			window["-AUTOCONNECT-"].update(visible = False)
		if event == "-CONNECT_BUTTON-":
			if values["-AUTOCONNECT-"]:
				settings["DefaultConnect"] = server
				write_settings()
			window.close()
			return server
		to_sleep = 1/30 - (time.time() - time_started)
		if to_sleep > 0:
			time.sleep(to_sleep)
	window.close()

async def main():
	read_settings()
	ip = await connect_window()
	client = EchoAPI.client(ip)

	@client.event.on_message()
	async def on_message(message):
		global inbox_value
		inbox_value = "-"*15+"\n"+f"from {message.author.username}:{message.author.public_hash}"+"\n"+message.content.replace("-"*15, "")+"\n"+inbox_value

	@client.event.on_ready()
	async def on_ready():
		await main_window()

	await login_prompt(client)
	await client.async_start()


if __name__ == "__main__":
	inbox_value = "-"*15+"\n"
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		pass
