# Interfaces to ease communication between server and client. Might be insecure...
import json

class folder:
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)
class default_request_interface:
	json = None #dict
	data = None #either hashmap raw bytes
	headers = None # Hashmep {HeaderName: HeaderValue
	handler = None # web_handler object
	_data_to_send = None # I heard that strings work very... Weird in python. Better to ensure everything is ok
	_headers_to_send = None # Hashmap {HeaderName: HeaderValue}
	path = None
	client_address = None
	def __init__(self, handler):
		self.handler = handler
		self._data_to_send = b""
		self._headers_to_send = {}
		self.path = self.handler.path.split("?")[0] #only the url without the data.
		self.headers = {}
		for header in self.handler.headers.keys(): #since handler's headers arent dict it needs to be here
			self.headers[header] = self.handler.headers[header]
		self.client_address = folder(ip = handler.client_address[0], port = handler.client_address[1])
		self._parse_data() # Retrive data based on request type. Specified in sub classes
	def write(self, data, codec = None):
		if not codec: #once again I want to eradicate unexpected behaviour.
			codec = "utf-8"
		if type(data) not in [str, bytes]:
			raise TypeError(f"Unexpected type. Expected: str or bytes; Got: {type(data)}")
		self._data_to_send += data if type(data) == bytes else data.encode(codec)

	def header(self, header, value):
		self._headers_to_send[header] = value

	def finish(self, code, autoset_content_length = True):
		if autoset_content_length and "Content-Length" not in self._headers_to_send:
			self._headers_to_send["Content-Length"] = len(self._data_to_send) #set content length if it isnt set already
		self.handler.send_response(code) #send code
		for header in self._headers_to_send.keys(): #send recorded headers
			self.handler.send_header(header, self._headers_to_send[header]) #kind of lame but I have no idea how to do otherwise
		self.handler.end_headers()
		self.handler.wfile.write(self._data_to_send) #send recorded data
	def verify(self, required_keys):
		if type(self.json) != dict:
			raise TypeError("Can not verify non-json data")
		keys = list(self.json.keys())
		keys.sort()
		required_keys.sort()
		return keys == required_keys

class get_interface(default_request_interface):
	def _parse_data(self):
		self.json = {}
		if self.handler.path.count("?") > 0:
			end_of_path = self.handler.path.split("?")[-1]
			key_value_pairs = end_of_path.split("&")
			for key_value_pair in key_value_pairs:
				key, value = key_value_pair.split("=")
				self.json[key] = value



class post_interface(default_request_interface):
	def _parse_data(self):
		self.data = self.handler.rfile.read(int(self.headers["Content-Length"]))
	def jsonize(self):
		splitdata = self.data.split(b"\n", 1)
		if len(splitdata) == 1:
			self.json = json.loads(splitdata[0])
			self.data = None
		else:
			self.json = json.loads(splitdata[0])
			self.data = splitdata[1]
