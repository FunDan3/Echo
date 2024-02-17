#! /usr/bin/python3
import os, pickle
def execute_script(script, update_files, to_remove, to_write):
	exec(script, globals(), {"update_files": update_files, "to_remove": to_remove, "to_write": to_write})
def execute_update(update_data):
	update = pickle.loads(update_data)
	if "preinstall" in update["scripts"]:
		execute_script(update["scripts"]["preinstall"], update["update_files"], update["to_remove"], update["to_write"])
	if "install" in update["scripts"]:
		execute_script(update["scripts"]["install"], update["update_files"], update["to_remove"], update["to_write"])
	if "postinstall" in update["scripts"]:
		execute_script(update["scripts"]["postinstall"], update["update_files"], update["to_remove"], update["to_write"])
	return update
