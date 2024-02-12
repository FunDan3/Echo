import PySimpleGUI as sg
import asyncio
import aiohttp
import json
from .. import common

async def server_test(server):
	async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(1)) as session:
		async with session.get(server+"echo-messager-server-info") as response:
			server_status = response.status
			server_response = await response.read()
	if server_status != 200:
		raise Exception(f"Server returned http status code {server_response.status_code}")
	return server_response

async def loop(settings, version, flavour):
	sg.theme("DarkAmber")
	if settings["DefaultConnect"]:
		return settings["DefaultConnect"]
	layout = [[sg.Text("Please choose the server to connect to. If you are uncertain leave default one")],
		  [sg.Input("foxomet.ru", key = "-SERVER_ADDRESS-")],
		  [sg.Text(key = "-OUTPUT-")],
		  [sg.Button("Connect", key = "-CONNECT_BUTTON-", visible = False), sg.Checkbox("Connect to this server automatically", default = True, key = "-AUTOCONNECT-", visible = False)]]
	window = sg.Window("Connect", layout)
	previous_server = ""
	while True:
		event, values = window.read(timeout = 0)
		if event == sg.WINDOW_CLOSED:
			raise KeyboardInterrupt("Program finished")
		try:
			server = f"https://{values['-SERVER_ADDRESS-']}:22389/"
			if server != previous_server and values["-SERVER_ADDRESS-"]:
				previous_server = server
				server_response, _ = await asyncio.gather(server_test(server), asyncio.sleep(1/30))
				server_data = json.loads(server_response)
				window["-OUTPUT-"].update("Server detected")
				if server_data["flavour"] != flavour:
					raise Exception(f"Server has {server_data['flavour']} which doesnt match with client flavour ({flavour})")
				if server_data["version"] != version:
					window["-OUTPUT-"].update(f"Server version is {server_data['version']} but client version is {version}")
					window["-CONNECT_BUTTON-"].update("Connect anyways", visible = True)
					window["-AUTOCONNECT-"].update(visible = True)
				else:
					window["-OUTPUT-"].update(f"Server is 100% comatible")
					window["-CONNECT_BUTTON-"].update("Connect", visible = True)
					window["-AUTOCONNECT-"].update(visible = True)
			else:
				await asyncio.sleep(1/30)
		except Exception as e:
			window["-OUTPUT-"].update(str(e))
			window["-CONNECT_BUTTON-"].update(visible = False)
			window["-AUTOCONNECT-"].update(visible = False)
		if event == "-CONNECT_BUTTON-":
			if values["-AUTOCONNECT-"]:
				settings["DefaultConnect"] = server
				common.write_settings(settings)
			window.close()
			return server
	window.close()
