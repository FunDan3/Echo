#! /usr/bin/python3

import components.cryptography.SymetricEncryptionLayer as SEL


import PySimpleGUI as sg
import pickle
import os
import asyncio
import hashlib
import aiohttp
import time
import json
from .. import common

async def password_change(client):
	layout = [[sg.Input(key = "-PASSWORD-")],
		  [sg.Button("Ok", key = "-CHANGE-")]]
	window = sg.Window("Change password", layout)
	while True:
		event, values = window.read(timeout = 0)
		if event == sg.WINDOW_CLOSED:
			break
		if event == "-CHANGE-":
			client.password = values["-PASSWORD-"]
			with open("container.epickle", "wb") as f:
				f.write(client.generate_container())
			break
		await asyncio.sleep(1/30)
	window.close()

async def set_description(client):
	layout = [[sg.Input(key = "-DESCRIPTION-")],
		  [sg.Text("", key = "-OUTPUT-")],
		  [sg.Button("Ok", key = "-SET-")]]
	window = sg.Window("Change description", layout)
	while True:
		event, values = window.read(timeout = 0)
		if event == sg.WINDOW_CLOSED:
			break
		if event == "-SET-":
			try:
				await client.set_description(values["-DESCRIPTION-"])
				break
			except Exception as e:
				window["-OUTPUT-"].update(str(e))
		await asyncio.sleep(1/30)
	window.close()


async def loop(client, inbox_value):
	previous_user_name = " "
	message_tab = [[sg.Text("User:", size = (10, 1)), sg.Input(key = "-USER-")],
		       [sg.Text("", key = "-DESCRIPTION-")],
		       [sg.Text("", key = "-PUBLIC_HASH-")],
		       [sg.Text("", key = "-KEM_ALGO-")],
		       [sg.Text("", key = "-SIG_ALGO-")],
		       [sg.Multiline(key = "-MESSAGE-", size = (70, 10))],
		       [sg.Button("Send", key = "-SEND-", visible = False)]]
	inbox_tab = [[sg.Text("", size = (70, 20), key = "-INBOX-")]]
	account_tab = [[sg.Button("Change account description", key = "-CHANGE_DESCRIPTION-")],
		       [sg.Button("Change container password", key = "-CHANGE_PASSWORD-")],
		       [sg.Button("Delete my account", key = "-DELETE-", button_color = ("#222222", "#FF0000"))]]

	layout = [[sg.TabGroup([[sg.Tab("Send message", message_tab), sg.Tab("Inbox", inbox_tab), sg.Tab("Account", account_tab)]])]]
	window = sg.Window("Echo messager", layout)
	FirstAccountDeletePush = True
	while True:
		event, values = window.read(timeout = 0)
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		window["-INBOX-"].update(inbox_value[0])
		if values["-USER-"] != previous_user_name:
			previous_user_name = values["-USER-"]
			try:
				user, _ = await asyncio.gather(client.fetch_user(values["-USER-"]), asyncio.sleep(1/30))
				window["-DESCRIPTION-"].update(user.description)
				window["-PUBLIC_HASH-"].update(user.public_hash, visible = True)
				window["-KEM_ALGO-"].update(user.kem_algorithm, visible = True)
				window["-SIG_ALGO-"].update(user.sig_algorithm, visible = True)
				window["-SEND-"].update(visible = True)
			except Exception as e:
				window["-DESCRIPTION-"].update(str(e))
				window["-SEND-"].update(visible = False)
				window["-KEM_ALGO-"].update(visible = False)
				window["-SIG_ALGO-"].update(visible = False)
				window["-PUBLIC_HASH-"].update(visible = False)
		else:
			await asyncio.sleep(1/30)
		if event == "-CHANGE_DESCRIPTION-":
			common.async_in_background(set_description(client))
		if event == "-CHANGE_PASSWORD-":
			common.async_in_background(password_change(client))
		if event == "-DELETE-":
			if FirstAccountDeletePush:
				window["-DELETE-"].update("REALLY delete my account")
				FirstAccountDeletePush = False
			else:
				await client.delete()
				os.remove("./container.epickle")
				raise KeyboardInterrupt("Program finished")
		if event == "-SEND-":
			user = await client.fetch_user(values["-USER-"])
			await user.dm_text(values["-MESSAGE-"])
			window["-MESSAGE-"].update("")
			window["-USER-"].update("")
			window["-PUBLIC_HASH-"].update("Message have been sent")
			window["-SEND-"].update(visible = False)
			window["-KEM_ALGO-"].update(visible = False)
			window["-SIG_ALGO-"].update(visible = False)

			previous_user_name = ""
	window.close()
