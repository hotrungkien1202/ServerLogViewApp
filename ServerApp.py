from flask import Flask, render_template
import json
from flask_cors import CORS
import os
app = Flask(__name__)
CORS(app)
baseURL = "./output"

@app.route('/filenames/<parentFolder>/<time>', methods = ['GET'])
def get_file_name(parentFolder, time):
	resuslt = []
	fileNames = os.listdir(baseURL + "/" + parentFolder)
	time_start = time + "0000"
	time_end = str(int(time)+1) + "0000"
	for filename in fileNames:
		file_time = filename.split(".")[0].split("_")[3]
		if int(time_start) <= int(file_time) <= int(time_end):
			resuslt.append(filename)
	x = sorted(resuslt, reverse=True)
	return  json.dumps(x)

@app.route('/foldernames', methods = ['GET'])
def get_folder_name():
	foldernames = os.listdir(baseURL)
	foldernames.sort(reverse=True)
	return json.dumps(foldernames)

@app.route('/filecontent/<parentFolder>/<filename>', methods = ['GET'])
def get_log_content(parentFolder, filename):
	path = baseURL + "/" + parentFolder + "/" + filename
	data_file = read_json_from_file(path)
	input = data_file['input'][0]
	hcOutputData = data_file['hc_output'][0]
	resuslt = {}
	tasks = input['tasks']
	resources = input['resources']
	index = 1;
	for hc in hcOutputData:
		if len(hc['request_id']) > 1:
			if hc['emp_id'] != "0":
				if hc["emp_id"] in resuslt:
					print('check ...', hc['request_id'])
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
	return json.dumps(rs)

def custom_cmp(json):
	try:
		return len(json["emp_id"])
	except Exception:
		return 0

def read_json_from_file(path):
	try:
		with open(path) as json_file:
			return json.load(json_file)
	except:
		print('Cant read this file')

def get_customer_level_by_request_id(tasks, request_id):
	for task in tasks:
		if int(task['request_id']) == int(request_id):
			return task['vip2'], task['number_emp_needed'], task['sub_type_1']
	return 0,0,0

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
			tup = get_customer_level_by_request_id(tasks, request_id)
			print(tup)
			rs['customer_level'] = tup[0]
			rs['number_of_emp'] = tup[1]
			rs['sub_type'] = tup[2]
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

if __name__ == '__main__':
   app.run()