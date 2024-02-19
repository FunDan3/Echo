#! /usr/bin/python3
# To install pysimplegui for windows use pip3 install "pysimplegui<5.0.0" due to some licensing.
program_version = "0.0.2"
program_flavour = "vanilla"
update_server = "foxomet.ru"

import components.cryptography.SymetricEncryptionLayer as SEL
from components import common

from components.windows import connect_window
from components.windows import banner_window
from components.windows import login_window
from components.windows import main_window

import PySimpleGUI as sg
import pickle
import os
import asyncio
import hashlib
import aiohttp
import time
import json
import subprocess

async def main():
	print(f"Echo {program_version} ({program_flavour})")
	settings = common.read_settings()

	ip = await connect_window.loop(settings, program_version, program_flavour)
	client = EchoAPI.client(ip)
	common.async_in_background(banner_window.loop(client, settings))
	await login_window.loop(client, settings)

	@client.event.on_message()
	async def on_message(message):
		global inbox_value
		inbox_value[0] = "-"*15+"\n"+f"from {message.author.username}:{message.author.public_hash}"+"\n"+message.content.replace("-"*15, "")+"\n"+inbox_value[0]

	@client.event.on_ready()
	async def on_ready():
		await asyncio.gather(main_window.loop(client, inbox_value))

	await client.async_start()


if __name__ == "__main__":
	import EchoAPI
	inbox_value = ["-"*15+"\n"]
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		if os.name == "posix":
			subprocess.Popen(["./update"])
		else:
			subprocess.Popen(["./update.exe"])
