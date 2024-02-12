import PySimpleGUI as sg
import os
from .. import common

async def loop(client):
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
