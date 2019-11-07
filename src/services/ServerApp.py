import datetime
import json
import os

import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
baseURL = "./output"


@app.route('/filenames/<parentFolder>/<time>/<block>', methods=['GET'])
def get_file(parentFolder, time, block):
    resuslt = []
    fileNames = os.listdir(baseURL + "/" + parentFolder)
    time_start = time + "0000"
    time_end = str(int(time) + 1) + "0000"
    for filename in fileNames:
        file_time = filename.split(".")[0].split("_")[3]
        if int(time_start) <= int(file_time) <= int(time_end) and block in filename:
            path = baseURL + "/" + parentFolder + "/" + filename
            data = read_json_from_file(path)
            if not isinstance(data['hc_output'][0], (list,)):
                hcOutputData = data['hc_output']
            else:
                hcOutputData = data['hc_output'][0]
            file = {}
            file['file_name'] = filename;
            file['load_factor'] = 0;
            file['version'] = data['version']
            try:
                for hc in hcOutputData:
                    if hc['error_code'] == 0 and not hc['load_factor'] is "":
                        file['load_factor'] = hc['load_factor']
                        break
            except Exception as e:
                pass
            resuslt.append(file);
    resuslt.sort(key=lambda x: x['file_name'], reverse=True)
    return json.dumps(resuslt)


@app.route('/foldernames', methods=['GET'])
def get_folder_name():
    foldernames = os.listdir(baseURL)
    foldernames.sort(reverse=True)
    return json.dumps(foldernames)


@app.route('/blocks/<parentFolder>/<time>', methods=['GET'])
def get_blocks(parentFolder, time):
    resuslt = []
    fileNames = os.listdir(baseURL + "/" + parentFolder)
    time_start = time + "0000"
    time_end = str(int(time) + 1) + "0000"
    for filename in fileNames:
        file_time = filename.split(".")[0].split("_")[3]
        if int(time_start) <= int(file_time) <= int(time_end):
            path = baseURL + "/" + parentFolder + "/" + filename
            block = {}
            data = read_json_from_file(path)
            input = data['input'][0]
            block['block_id'] = input['block_id']
            block['block_name'] = input['block_name']
            block['block_gray'] = input['block_gray']
            block['block_distance'] = input['block_distance']
            block['block_ability'] = input['block_ability']
            block['res_time'] = input['res_time']
            if not any(r['block_id'] == block['block_id'] for r in resuslt):
                resuslt.append(block)
    resuslt.sort(key=lambda x: x['block_name'])
    return json.dumps(resuslt)


@app.route('/filecontent/<parentFolder>/<filename>', methods=['GET'])
def get_log_content(parentFolder, filename):
    path = baseURL + "/" + parentFolder + "/" + filename
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
                        resuslt[hc["emp_id"]]['tasks'].append(
                            get_assigned_task_by_request_id(hcOutputData, tasks, hc['request_id']))
                    else:
                        employee = get_employee_by_emp_id(resources, hc['emp_id'])
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
        if resource['emp_id'] not in resuslt:
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
    except:
        print('Cant read this file')


def get_customer_level_by_request_id(tasks, request_id):
    for task in tasks:
        if int(task['request_id']) == int(request_id):
            return task['vip2'], task['number_emp_needed'], task['sub_type_1'], task['reason_out_case_desc'], task[
                'appointmentdate'], task['sub_type_2'], task['emp_speciallized'], task['contract']
    return 0, 0, 0, 0, 0, 0, 0


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
            rs['customer_level'] = tup[0]
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


@app.route('/download/<parentFolder>/<filename>', methods=['GET'])
def download_input(parentFolder, filename):
    path = baseURL + "/" + parentFolder + "/" + filename
    data_file = read_json_from_file(path)
    input = data_file['input']
    return json.dumps(input, sort_keys=True, indent=4)


@app.route('/contract/<contract_id>', methods=['GET'])
def get_files_by_contract(contract_id):
    timenow = datetime.datetime.now()
    parentFolder = timenow.strftime('%Y%m%d')
    fileNames = os.listdir(baseURL + "/" + parentFolder)
    fileNames.sort(reverse=True)
    print(fileNames[0], len(fileNames))
    # return "OK"
    count = 0;
    result = []
    for file in fileNames:
        path = baseURL + "/" + parentFolder + "/" + file
        data = read_json_from_file(path)
        input_ = data['input'][0]
        tasks = input_['tasks']
        for task in tasks:
            if str(task['contract']) == str(contract_id):
                result.append(file)
                count += 1
                if count == 10:
                    return json.dumps(result)
                break
    return json.dumps(result)


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
