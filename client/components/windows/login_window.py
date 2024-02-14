import PySimpleGUI as sg
import os
import asyncio
from .. import common

async def loop(client, settings):
	sg.theme("DarkAmber")
	if os.path.exists("./container.epickle"):
		layout = [[sg.Text("Container found. Please enter password to decrypt it")],
			  [sg.Input(key = "-PASSWORD-")],
			  [sg.Text(key = "-OUTPUT-")],
			  [sg.Button("Ok", key = "-LOGIN_BUTTON-", visible = False), sg.Checkbox("Login automatically as soon as container was decrypted", key = "-AUTOLOGIN-", visible = False, default = True)]]
		window = sg.Window("Login", layout)
		previous_password = None
		with open("./container.epickle", "rb") as container_file:
			container_content = container_file.read()
		while True:
			event, values = window.read(timeout = 0)
			if event == sg.WINDOW_CLOSED:
				raise KeyboardInterrupt("Program finished")
			if previous_password!=values["-PASSWORD-"]:
				previous_password = values["-PASSWORD-"]
				validated = client.is_valid_container(container_content, values["-PASSWORD-"])
				if validated == "yes":
					window["-OUTPUT-"].update("Container decrypted. You can log in now.")
					window["-LOGIN_BUTTON-"].update(visible = True)
					window["-AUTOLOGIN-"].update(visible = True)
					if settings["AutoLogin"]:
						try:
							await client.login(container_content, values["-PASSWORD-"])
							break
						except Exception as e:
							window["-OUTPUT-"].update(str(e))
				else:
					valid_password = False
					window["-OUTPUT-"].update(validated)
					window["-AUTOLOGIN-"].update(visible = False)
					window["-LOGIN_BUTTON-"].update(visible = False)
			if event == "-LOGIN_BUTTON-":
					try:
						await client.login(container_content, values["-PASSWORD-"])
						if values["-AUTOLOGIN-"] and not settings["AutoLogin"]:
							settings["AutoLogin"] = True
							common.write_settings(settings)
						break
					except Exception as e:
						window["-OUTPUT-"].update(str(e))
			await asyncio.sleep(1/30)
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
