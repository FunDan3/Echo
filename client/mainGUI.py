#! /usr/bin/python3
# To install pysimplegui for windows use pip3 install "pysimplegui<5.0.0" due to some licensing.
import EchoAPI
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

program_version = "0.0.2"
program_flavour = "vanilla"
settings = common.read_settings()

async def main():
	inbox_value = ["-"*15+"\n"]
	ip = await connect_window.loop(settings, program_version, program_flavour)
	client = EchoAPI.client(ip)
	await banner_window.loop(client, settings)
	await login_window.loop(client, settings)

	@client.event.on_message()
	async def on_message(message):
		global inbox_value
		inbox_value[0] = "-"*15+"\n"+f"from {message.author.username}:{message.author.public_hash}"+"\n"+message.content.replace("-"*15, "")+"\n"+inbox_value

	@client.event.on_ready()
	async def on_ready():
		await main_window.loop(client, inbox_value)

	await client.async_start()


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		pass
