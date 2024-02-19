import json
import random
import asyncio
def read_settings():
	try:
		with open("./settings.json", "rb") as f:
			settings = json.loads(f.read())
	except Exception:
		print("Settings file is corrupted or doesnt exist. Resetting them")
		settings = {"DefaultConnect": "", "DontShowBannersOn": [], "AutoLogin": False}
		write_settings(settings)
	return settings

def write_settings(settings): #settings are probably not worth encrypting
	with open("./settings.json", "wb") as f:
		f.write(json.dumps(settings).encode("utf-8"))
def async_in_background(coro):
	loop = asyncio.get_event_loop()
	asyncio.ensure_future(coro, loop = loop)
