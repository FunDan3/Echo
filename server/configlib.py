# Simple interface to interact with json files
import os
import json


class DictLayer:
	filename = None #String (path)
	data = None #Dict
	autosave = None #Bool
	def __init__(self, filename, template = None, autosave = False):
		if not template:
			template = {}
		self.filename = filename
		if not os.path.exists(filename):
			self._GenerateFile(template) #self.data would be equal to template
		else:
			self.data = self._read()
		self.autosave = autosave
	def _GenerateFile(self, template):
		splitpath = self.filename.split("/")
		past = ""
		for directory in splitpath[:len(splitpath)-1]: #everything except the last element
			if not os.path.exists(past + directory):
				os.mkdir(past + directory)
			past += directory + "/"
		with open(self.filename, "w") as f:
			json.dump(template, f)
		self.data = template
	def _read(self):
		with open(self.filename, "rb") as f:
			return json.load(f)
	def save(self):
		with open(self.filename, "w") as f:
			json.dump(self.data, f)
	#dict methods
	def clear(self):
		self.data.clear()
	def items(self):
		return self.data.items()
	def keys(self):
		return self.data.keys()
	def values(self):
		return self.data.values()
	def __getitem__(self, item):
		return self.data[item]
	def __contains__(self, item):
		return self.data.__contains__(self, item)
	def __setitem__(self, item, data):
		self.data[item] = data
		if self.autosave:
			self.save()
	#personal methods
	def __str__(self):
		return str(self.data)
