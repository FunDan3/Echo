#! /usr/bin/python3

import os
import sys

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
	os.system("pyinstaller --onefile --windowed mainGUI.py")
	with open("/usr/local/lib/liboqs.so", "rb") as read:
		with open("./dist/liboqs.so", "wb") as write:
			write.write(read.read())
	remove("./mainGUI.spec")
	remove("./build")
	remove("./__pycache__")
def compile_for_windows():
	python_lib_path = os.path.expanduser(f"~\\AppData\\Roaming\\Python\\Python{sys.version_info.major}{sys.version_info.minor}\\site-packages\\")
	oqs_path = python_lib_path + "oqs\\oqs.py"
	print(oqs_path)
	patch_oqs_lib(oqs_path)
	try:
		remove("./dist/")
	except Exception:
		pass
	os.system("pyinstaller --onefile --windowed mainGUI.py")
	with open("liboqs.dll", "rb") as read:
		with open("dist\\liboqs.dll", "wb") as write:
			write.write(read.read())
	remove("./mainGUI.spec")
	remove("./build")
	remove("./__pycache__")


if __name__ == "__main__":
	if os.name == "posix":
		compile_for_linux()
	if os.name == "nt":
		compile_for_windows()
