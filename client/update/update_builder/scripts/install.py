import os

def remove(path):
	global remove
	if os.path.isdir(path):
		path = path + ("/" if not path.endswith("/") else "")
		if os.path.exists(path):
			for file in os.listdir(path):
				file_path = path+file
				remove(file_path)
			os.rmdir(path)
			print(f"removed {path}")
		else:
			print(f"{path} doesnt exist so werent removed")

	else:
		if os.path.exists(path):
			os.remove(path)
			print(f"removed {path}")
		else:
			print(f"{path} doesnt exist so werent removed")

def write(path, data):
	previous_directory = ""
	for directory in path.split("/")[:path.count("/")]:
		if not os.path.exists(previous_directory+directory):
			os.mkdir(previous_directory+directory)
			print(f"created directory {previous_directory}{directory}/")
		previous_directory+=f"{directory}/"
	if os.path.exists(path):
		with open(path, "rb") as read:
			read_data = read.read()
		if read_data != data:
			with open(path, "wb") as f:
				f.write(data)
			print(f"written {path}")
		else:
			print(f"{path} already exists and updated.")
	else:
		with open(path, "wb") as f:
			f.write(data)
		print(f"written {path}")

for path in to_remove:
	remove(path)

for path in to_write:
	write(path, update_files[path])
