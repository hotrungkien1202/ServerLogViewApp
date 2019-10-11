from flask import Flask, render_template
import json
from flask_cors import CORS
import os
import datetime
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
app = Flask(__name__)
CORS(app)
baseURL = "./output"

@app.route('/filenames/<parentFolder>/<time>/<block>', methods = ['GET'])
def get_file(parentFolder, time, block):
	result = []
	fileNames = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block)
	for filename in fileNames:
		path = baseURL + "/" + parentFolder + "/" + time + "/" + block + "/" + filename
		data = read_json_from_file(path)
		if not isinstance(data['hc_output'][0], (list,)):
			hcOutputData = data['hc_output']
		else:
			hcOutputData = data['hc_output'][0]
		file = {}
		file['file_name'] = filename;
		file['load_factor'] = 0;
		file['res_time'] = data['input'][0]['res_time']
		try:
			for hc in hcOutputData:
				if hc['error_code'] == 0 and not hc['load_factor'] is "":
					file['load_factor'] = hc['load_factor']
					break
		except Exception as e:
			pass
		result.append(file);
	result.sort(key=lambda x: x['file_name'], reverse = True)
	return  json.dumps(result)

@app.route('/foldernames', methods = ['GET'])
def get_folder_name():
	foldernames = os.listdir(baseURL)
	foldernames.sort(reverse=True)
	return json.dumps(foldernames)

@app.route('/blocks/<parentFolder>/<time>', methods=['GET'])
def get_blocks(parentFolder, time):
	result = []
	try:
		blocks = os.listdir(baseURL + "/" + parentFolder + "/" + time)
		for block in blocks:
			filenames = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block)
			filename = filenames[0]
			path = baseURL + "/" + parentFolder + "/" + time + "/" + block + "/" + filename
			b = {}
			data = read_json_from_file(path)
			input_ = data['input'][0]
			b['block_id'] = input_['block_id']
			b['block_name'] = input_['block_name']
			b['block_distance'] = input_['block_distance']
			b['block_ability'] = input_['block_ability']
			b['version'] = data['version']
			if not any(r['block_id'] == b['block_id'] for r in result):
				result.append(b)
		result.sort(key=lambda x: x['block_name'])
	except Exception as e:
		pass
	return json.dumps(result)

@app.route('/filecontent/<parentFolder>/<filename>', methods = ['GET'])
def get_log_content(parentFolder, filename):
	name = filename.split(".")[0]
	file_time = name.split("_")[3][0:2]
	file_block = name.split("_")[4]
	path = baseURL + "/" + parentFolder + "/" + file_time + "/" + file_block + "/" + filename
	data_file = read_json_from_file(path)
	input = data_file['input'][0]
	if not isinstance(data_file['hc_output'][0], (list,)):
		hcOutputData = data_file['hc_output']
	else:
		hcOutputData = data_file['hc_output'][0]
	tasks = input['tasks']
	resources = input['resources']
	index = 1;
	load_factor = ""
	resuslt = {}
	try:
		for hc in hcOutputData:
			if len(hc['request_id']) > 1:
				if hc['emp_id'] != "0":
					if hc["emp_id"] in resuslt:
						resuslt[hc["emp_id"]]['tasks'].append(get_assigned_task_by_request_id(hcOutputData, tasks, hc['request_id']))
					else:
						employee = get_employee_by_emp_id(resources,hc['emp_id'])
						employee['tasks'] = [get_assigned_task_by_request_id(hcOutputData, tasks, hc['request_id'])]
						resuslt[hc["emp_id"]] = employee
				else:
					employee = {}
					employee['emp_id'] = ""
					employee['emp_available'] = ""
					employee['emp_type'] = ""
					employee['emp_rank'] = ""
					employee['emp_level'] = ""
					employee['emp_status'] = ""
					employee['emp_assigned'] = ""
					employee['tasks'] = [get_assigned_task_by_request_id(hcOutputData, tasks, hc['request_id'])]
					resuslt[str(index)] = employee
					index += 1
	except Exception as e:
		pass
	for resource in resources:
		if  resource['emp_id'] not in resuslt:
			employee = {}
			employee['emp_id'] = resource['emp_id']
			employee['emp_available'] = resource['available']
			employee['emp_type'] = resource['type']
			employee['emp_rank'] = resource['rank']
			employee['emp_level'] = resource['emp_level']
			employee['emp_status'] = resource['emp_status']
			employee['emp_assigned'] = resource['emp_assigned']
			employee['tasks'] = []
			resuslt[resource['emp_id']] = employee
	rs = []
	for x in resuslt.values():
		rs.append(x)
	rs.sort(key=custom_cmp, reverse=True)
	final_rs = {}
	final_rs['load_factor'] = load_factor
	final_rs['employees'] = rs
	return json.dumps(final_rs)

def custom_cmp(json):
	try:
		return len(json["emp_id"])
	except Exception:
		return 0

def read_json_from_file(path):
	try:
		with open(path) as json_file:
			return json.load(json_file)
	except Exception as e:
		raise e

def get_customer_level_by_request_id(tasks, request_id):
	for task in tasks:
		if int(task['request_id']) == int(request_id):
			return task['manual_priority'], task['number_emp_needed'], task['sub_type_1'], task['reason_out_case_desc'], task['appointmentdate'], task['sub_type_2'], task['emp_speciallized'], task['contract']
	return 0,0,0,0,0,0,0

def get_assigned_task_by_request_id(hcOutputData, tasks, request_id):
	rs = {}
	for hc in hcOutputData:
		if int(hc["request_id"]) == int(request_id):
			rs['request_id'] = hc["request_id"]
			rs['start_time'] = hc['start_time']
			rs['checkin_time'] = hc['checkin_time']
			rs['checkout_time'] = hc['checkout_time']
			rs['task_type'] = hc['type']
			rs['assigned'] = hc['assigned']
			rs['late_time'] = hc['late_time']
			tup = get_customer_level_by_request_id(tasks, request_id)
			rs['manual_priority'] = tup[0]
			rs['number_of_emp'] = tup[1]
			rs['sub_type'] = tup[2]
			rs['reason_outcase'] = tup[3]
			rs['appoiment_date'] = tup[4]
			rs['sub_type2'] = tup[5]
			rs['emp_speciallized'] = tup[6]
			rs['contract'] = tup[7]
	return rs

def get_employee_by_emp_id(resources, emp_id):
	employee = {}
	for resource in resources:
		if resource["emp_id"] == emp_id:
			employee['emp_id'] = resource['emp_id']
			employee['emp_available'] = resource['available']
			employee['emp_type'] = resource['type']
			employee['emp_rank'] = resource['rank']
			employee['emp_level'] = resource['emp_level']
			employee['emp_status'] = resource['emp_status']
			employee['emp_assigned'] = resource['emp_assigned']
	return employee

@app.route('/download/<parentFolder>/<filename>', methods = ['GET'])
def download_input(parentFolder, filename):
	name = filename.split(".")[0]
	file_time = name.split("_")[3][0:2]
	file_block = name.split("_")[4]
	path = baseURL + "/" + parentFolder + "/" + file_time + "/" + file_block + "/" + filename
	data_file = read_json_from_file(path)
	input = data_file['input']
	return json.dumps(input, sort_keys=True, indent=4)

@app.route('/contract/<parentFolder>/<contract_id>', methods = ['GET'])
def get_files_by_contract(parentFolder, contract_id):
	fileNames = []
	command = 'grep -E "\\"contract\\"\s*\:\s*\\"' + contract_id + '\\"" -rl ./output/' + parentFolder + "/ > contract_data.txt"
	os.system(command)
	with open("contract_data.txt") as file:
		for line in file:
			ll = str(line).replace('\n', '').split("/")
			fileNames.append(ll[len(ll)-1])
	fileNames.sort(reverse = True)
	result = fileNames[0:10]
	return json.dumps(result)

@app.route('/summary/<parentFolder>/<time>', methods = ['GET'])
def statistic_assigned_task_for_employee(parentFolder, time):
	result = []
	try:
		blocks = os.listdir(baseURL + "/" + parentFolder + "/" + time)
		for block in blocks:
			capacity = 0
			obj = {}
			files = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block)
			files.sort()
			file = files[len(files)-1]
			path = baseURL + "/" + parentFolder + "/" + time + "/" + block + "/" + file
			data = read_json_from_file(path)
			resources = data["input"][0]["resources"]
			employees = []
			for resource in resources:
				employee = {}
				employee["emp_id"] = resource["emp_id"]
				employee["emp_assigned"] = resource["emp_assigned"]
				employee["emp_type"] = resource["type"]
				capacity += resource["emp_assigned"]
				employees.append(employee)
			employees.sort(key = lambda x : x["emp_assigned"], reverse = True)
			obj["block_id"] = data["input"][0]["block_id"]
			obj["block_name"] = data["input"][0]["block_name"]
			obj["employees"] = employees
			obj["capacity"] = "%.2f" % (capacity/float(len(employees)))
			result.append(obj)
			result.sort(key = lambda x: x['block_name'])
	except Exception as e:
		pass
	return json.dumps(result)

@app.route('/maps/<parentFolder>/<block_id>', methods = ['GET'])
def get_data_to_show_block_map(parentFolder, block_id):
	command = 'grep -E "\\"assigned\\"\s*\:\s*\\"1\\"" -rl ./output/' + parentFolder + "/*/" + block_id + "/ > map_block_data.txt"
	os.system(command)
	emp_dict = {}
	paths = []
	with open("map_block_data.txt") as file:
		for line in file:
			paths.append(str(line).replace('\n', ''))
	paths.sort()
	for path in paths:
		#print(path)
		content = read_json_from_file(path)
		hcOutput = content["hc_output"]
		for hc in hcOutput:
			if int(hc["assigned"]) == 1:
				obj = {}
				obj["emp_id"] = hc["emp_id"]
				obj["request_id"] = hc["request_id"]
				obj["cus_coordinate"] = hc["cus_coordinate"]
				obj["emp_distance"] = hc["emp_distance"]
				if hc["emp_id"] in emp_dict:					
					emp_dict[hc["emp_id"]].append(obj)
				else:
					emp_dict[hc["emp_id"]] = [obj]

	result = []
	for v in emp_dict.values():
		result.append(v)
	#result.sort(key = lambda x: x["start_time"])
	return json.dumps(result)

@app.route('/maps/<parentFolder>/<block_id>/<emp_id>', methods = ['GET'])
def get_data_to_show_map(parentFolder, block_id, emp_id):
	command = 'grep -E "\\"assigned\\"\s*\:\s*\\"1\\"" -rl ./output/' + parentFolder + "/*/" + block_id + "/ > map_data.txt"
	os.system(command)
	data = {}
	paths = []
	with open("map_data.txt") as file:
		for line in file:
			paths.append(str(line).replace('\n', ''))
	paths.sort()
	for path in paths:
		content = read_json_from_file(path)
		hcOutput = content["hc_output"]
		tasks = content["input"][0]["tasks"]
		for hc in hcOutput:
			if int(hc["assigned"]) == 1:
				if hc["request_id"] in data:
					del data[hc["request_id"]]
				if hc["emp_id"] == emp_id:
					obj = {}
					obj["cus_coordinate"] = hc["cus_coordinate"]
					obj["emp_distance"] = hc["emp_distance"]
					obj["task_type"] = hc["type"]
					obj["start_time"] = get_hour_and_minute_in_time(hc["start_time"])
					obj["checkout_time"] = get_hour_and_minute_in_time(hc["checkout_time"])
					obj["late_time"] = hc["late_time"]
					obj["appointmentdate"] = get_hour_and_minute_in_time(get_customer_level_by_request_id(tasks, hc["request_id"])[4])
					# print(obj["res_time"])
					data[hc["request_id"]] = obj
	result = []
	for v in data.values():
		result.append(v)
	result.sort(key = lambda x: x["start_time"])
	return json.dumps(result)

def get_hour_and_minute_in_time(custom_time):
	tmp = custom_time.strip().split(" ")[1]
	return tmp[0:5]

def start_tornado(app, port, force_https=False):

    if force_https:
        settings = dict(
            ssl_options={
                "certfile": os.path.join("../../data/.certs/domain.crt"),
                "keyfile": os.path.join("../../data/.certs/domain.key"),
            },
        )

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app), **settings)
    else:
        http_server = tornado.httpserver.HTTPServer(
            tornado.wsgi.WSGIContainer(app))

    http_server.listen(port)
    print("Starting Tornado server on port {}".format(port))
    tornado.ioloop.IOLoop.instance().start()
    print("Tornado server started on port {}".format(port))


if __name__ == '__main__':
   # app.run()
   start_tornado(app, 5005)