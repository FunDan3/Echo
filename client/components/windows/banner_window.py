#! /usr/bin/python3
import PySimpleGUI as sg
from .. import common

async def loop(client, settings):
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
				common.write_settings(settings)
			break
	window.close()
