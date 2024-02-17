#! /usr/bin/python3

import os
import sys
import json
from mainGUI import program_version
from mainGUI import update_server

def remove(path):
	if os.path.isdir(path):
		path = path + ("/" if not path.endswith("/") else "")
		filelist = os.listdir(path)
		for file in filelist:
			remove(path + file)
		os.rmdir(path)
	else:
		os.remove(path)

def patch_oqs_lib(path):
	original_import_snippet ="""import sys
import warnings"""
	fixed_import_snippet = """import sys
import os
import warnings"""
	original_code_snippet = '''def _load_shared_obj(name):
    """Attempts to load native OQS library."""
    paths = []

    # search typical locations
    paths += [ctu.find_library(name)]
    paths += [ctu.find_library("lib" + name)]
    dll = ct.windll if platform.system() == "Windows" else ct.cdll

    for path in paths:
        if path:
            lib = dll.LoadLibrary(path)
            return lib

    raise RuntimeError("No " + name + " shared libraries found")'''
	fixed_code_snippet = '''def _load_shared_obj(name):
    """Attempts to load native OQS library."""
    global_paths = []
    local_paths = []

    library_extension = ".dll" if platform.system() == "Windows" else ".so"

    # search typical locations
    local_paths += [f"./{name}{library_extension}"]
    local_paths += [f"./lib{name}{library_extension}"]

    global_paths += [ctu.find_library(name)]
    global_paths += [ctu.find_library("lib" + name)]
    dll = ct.windll if platform.system() == "Windows" else ct.cdll

    for path in local_paths:
        if os.path.exists(path):
            lib = dll.LoadLibrary(path)
            return lib

    for path in global_paths:
        if path:
            lib = dll.LoadLibrary(path)
            return lib

    raise RuntimeError("No " + name + " shared libraries found")'''
	with open(path, "r") as f:
		oqs_source_code = f.read()
	oqs_patched_code = oqs_source_code.replace(original_code_snippet, fixed_code_snippet).replace(original_import_snippet, fixed_import_snippet)
	if oqs_patched_code != oqs_source_code:
		print(oqs_patched_code)
		with open(path, "w") as f:
			f.write(oqs_patched_code)

def compile_for_linux():
	python_lib_path = os.path.expanduser(f"~/.local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/")
	oqs_path = python_lib_path + "oqs/oqs.py"
	patch_oqs_lib(oqs_path)
	try:
		remove("./dist/")
	except Exception:
		pass
	os.system("pyinstaller --windowed mainGUI.py") #nuitka seems to have hard time working with linux
	os.system("pyinstaller --onefile update/updater/update.py")
	remove("./build/")
	remove("./mainGUI.spec")
	remove("./update.spec")
	os.rename("./dist/mainGUI/", "./dist.temp/")
	os.rename("./dist/update", "./dist.temp/update")
	remove("./dist/")
	os.rename("./dist.temp/", "./dist/")
	with open("/usr/local/lib/liboqs.so", "rb") as read:
		with open("./dist/liboqs.so", "wb") as write:
			write.write(read.read())
	with open("./dist/updater_config.json", "w") as f:
		f.write(json.dumps({"server": update_server, "version": program_version}))
	#remove("./__pycache__/")
def compile_for_windows():
	python_lib_path = os.path.expanduser(f"~\\AppData\\Roaming\\Python\\Python{sys.version_info.major}{sys.version_info.minor}\\site-packages\\")
	oqs_path = python_lib_path + "oqs\\oqs.py"
	print(oqs_path)
	patch_oqs_lib(oqs_path)
	try:
		remove("./dist/")
	except Exception:
		pass
	os.system("nuitka --standalone --onefile update\\updater\\update.py")
	os.system("nuitka --standalone --enable-plugin=tk-inter --disable-console mainGUI.py")
	#liboqs is expected to be in the compilation folder by default
	with open("liboqs.dll", "rb") as read:
		with open("mainGUI.dist\\liboqs.dll", "wb") as write:
			write.write(read.read())
	remove("./mainGUI.build/")
	remove("./update.build/")
	remove("./update.dist/")
	remove("./update.onefile-build/")
	os.rename("mainGUI.dist", "dist")
	os.rename("./update.exe", "./dist/update.exe")
	with open("./dist/updater_config.json", "w") as f:
		f.write(json.dumps({"server": update_server, "version": program_version}))
if __name__ == "__main__":
	if os.name == "posix":
		compile_for_linux()
	if os.name == "nt":
		compile_for_windows()
