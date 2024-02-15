import os

def remove(path):
	global remove
	if os.path.isdir(path):
		path = path + ("/" if not path.endswith("/") else "")
		for file in os.listdir(path):
			file_path = path+file
			remove(file_path)
		os.rmdir(path)
	else:
		os.remove(path)
	print(f"removed {path}")

def write(path, data):
	previous_directory = ""
	for directory in path.split("/")[:path.count("/")]:
		if not os.path.exists(previous_directory+directory):
			os.mkdir(previous_directory+directory)
			print(f"created directory {previous_directory}{directory}/")
		previous_directory+=f"{directory}/"
	with open(path, "wb") as f:
		f.write(data)
	print(f"written {path}")

for path in to_remove:
	remove(path)

for path in to_write:
	write(path, update_files[path])
