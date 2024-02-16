from . import update_executor
import aiohttp
import platform
import asyncio

def GetFilename(program_version):
	bits = platform.architecture()[0]
	os = platform.system()
	if os == "Windows":
		os += platform.release()
	return f"EchoUpdate{os}{bits}-{program_version}.update"

async def RequestUpdateData(server, program_version):
	try:
		async with aiohttp.ClientSession() as session:
			url = f"https://{server}/EchoMessager/Updates/{GetFilename(program_version)}"
			print(f"Fetching update from {url}")
			async with session.get(url) as response:
				if response.status not in range(200, 300) and response.status!=404:
					raise Exception(f"Update failed with status code {response.status}")
				elif response.status == 404:
					raise Exception("No update")
				return await response.read()
	except Exception as e:
		print(e)
		return None

async def loop(server, program_version, delay = 5*60):
	while True:
		update = await RequestUpdateData(server, program_version)
		if update:
			print("Updating...")
			update_executor.execute_update(update) #For now I dont even ask. I add ability for user to cancel update later
			raise KeyboardInterrupt("Program finished")
		await asyncio.sleep(delay)
