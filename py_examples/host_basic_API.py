# -*- coding: utf-8 -*-
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
#{"1": "First", "2": "Second", "3": "Third", "4": "Fourth"}
with open("data.json") as data_file:
	data = json.load(data_file)

#Defining a HTTP request Handler class
class ServiceHandler(BaseHTTPRequestHandler):
	#sets basic headers for the server
	def _set_headers(self):
		self.send_response(200)
		self.send_header('Content-type','text/json')
		length = int(self.headers['Content-Length'])
		#reads the contents of the request
		content = self.rfile.read(length)
		temp = str(content).strip('b\'')
		self.end_headers()
		return temp
		
	def do_GET(self):
		#defining all the headers
		self.send_response(200)
		self.send_header('Content-type','text/json')
		self.end_headers()
		#prints all the keys and values of the json file
		self.wfile.write(json.dumps(data).encode())
		
	def do_VIEW(self):
		#dict var. for pretty print
		display = {}
		temp = self._set_headers()
		#check if the key is present in the dictionary
		if temp in data:
			display[temp] = data[temp]
			#print the keys required from the json file
			self.wfile.write(json.dumps(display).encode())
		else:
			error = "NOT FOUND!"
			self.wfile.write(bytes(error,'utf-8'))
			self.send_response(404)
			
	def do_POST(self):
		temp = self._set_headers()
		key=0
		#getting key and value of the data dictionary
		for key,value in data.items():
			pass
		index = int(key)+1
		data[str(index)]=str(temp)
		#write the changes to the json file
		with open("data.json",'w+') as file_data:
			json.dump(data,file_data)
		self.wfile.write(json.dumps(data[str(index)]).encode())
	
	def do_PUT(self):
		temp = self._set_headers()
		#seprating input into key and value
		x = temp[:1]
		y = temp[2:]
		#check if key is in data
		if x in data:
			data[x] = y
			#write the changes to file
			with open("data.json",'w+') as file_data:
				json.dump(data,file_data)
			self.wfile.write(json.dumps(data[str(x)]).encode())
		else:
			error = "NOT FOUND!"
			self.wfile.write(bytes(error,'utf-8'))
			self.send_response(404)

	def do_DELETE(self):
		temp = self._set_headers()
		#check if the key is present in the dictionary
		if temp in data:
			del data[temp]
			#write the changes to json file
			with open("data.json",'w+') as file_data:
				json.dump(data,file_data)
		else:
			error = "NOT FOUND!"
			self.wfile.write(bytes(error,'utf-8'))
			self.send_response(404)
server = HTTPServer(('127.0.0.1',8080),ServiceHandler)
server.serve_forever()