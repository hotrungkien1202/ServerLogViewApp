from flask import Flask, render_template
import json
from flask_cors import CORS
import os
import datetime
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
from common.utils import *
from models.log_emps import *

app = Flask(__name__)
CORS(app)
baseURL = "./services/output"

@app.route('/block_all/<parentFolder>/<time>', methods = ['GET'])
def get_all_blocks_data(parentFolder, time) :
    result = []
    try:
        blocks = os.listdir(baseURL + "/" + parentFolder + "/" + time)
        for block in blocks:
            filenames = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block)
            filenames.sort(reverse=True)
            filename = filenames[0]
            path = baseURL + "/" + parentFolder + "/" + time + "/" + block + "/" + filename
            #print(path)
            b = {}
            data = read_json_from_file(path)
            input_ = data['input'][0]
            hc_output_ = data['hc_output']
            b['block_id'] = input_['block_id']
            b['block_name'] = input_['block_name']
            b['block_distance'] = input_['block_distance']
            b['block_center'] = input_['block_center']
            b['version'] = data['version']
            b['emp_count'] = len(input_["resources"])
            load_factor = 0.0
            if len(hc_output_) > 0:
                load_factor = hc_output_[0]["load_factor"]
            b['load_factor'] = load_factor
            # load factor

            if not any(r['block_id'] == b['block_id'] for r in result):
                result.append(b)
        result.sort(key=lambda x: x['load_factor'])
    except Exception as e:
        pass
    return json.dumps(result)

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
        file['file_name'] = filename
        file['load_factor'] = 0
        file['res_time'] = data['input'][0]['res_time']
        try:
            for hc in hcOutputData:
                if hc['error_code'] == 0 and not hc['load_factor'] is "":
                    file['load_factor'] = hc['load_factor']
                    break
        except Exception as e:
            pass
        result.append(file)
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
            filename = max(filenames)
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
    try:
        data_file = read_json_from_file(path)
        input = data_file['input'][0]
        if not isinstance(data_file['hc_output'][0], (list,)):
            hcOutputData = data_file['hc_output']
        else:
            hcOutputData = data_file['hc_output'][0]
        tasks = input['tasks']
        resources = input['resources']
        index = 1
        load_factor = ""
        resuslt = {}
        for hc in hcOutputData:
            #print("for1 ", hc["request_id"])
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
            #employee['emp_rank'] = resource['rank']
            employee['emp_level'] = resource['emp_level']
            employee['emp_status'] = resource['emp_status']
            employee['emp_assigned'] = resource.get('emp_assigned', 0)
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
            return task['manual_priority'], 0, task['sub_type_1'], task['reason_out_case_type'], task['appointmentdate'], task['sub_type_2'], task['emp_speciallized'], task['contract'], task["date_confirmed"], task['appointmentdate2']
    return 0,0,0,0,0,0,0

def get_assigned_task_by_request_id(hcOutputData, tasks, request_id):
    #print(request_id)
    rs = {}
    for hc in hcOutputData:
        if int(hc["request_id"]) == int(request_id):
            #print("exists")
            rs['request_id'] = hc["request_id"]
            rs['start_time'] = hc['start_time']
            rs['checkin_time'] = hc['checkin_time']
            rs['checkout_time'] = hc['checkout_time']
            rs['task_type'] = hc['type']
            rs['assigned'] = hc['assigned']
            rs['late_time'] = hc['late_time']
            rs['priority'] = hc['priority']
            tup = get_customer_level_by_request_id(tasks, request_id)
            rs['manual_priority'] = tup[0]
            rs['number_of_emp'] = tup[1]
            rs['sub_type'] = tup[2]
            rs['reason_outcase'] = tup[3]
            rs['appoiment_date'] = tup[4]
            rs['sub_type2'] = tup[5]
            rs['emp_speciallized'] = tup[6]
            rs['contract'] = tup[7]
            rs['appoiment_date2'] = tup[9]
    return rs

def get_employee_by_emp_id(resources, emp_id):
    employee = {}
    for resource in resources:
        if resource["emp_id"] == emp_id:
            employee['emp_id'] = resource['emp_id']
            employee['emp_available'] = resource['available']
            employee['emp_type'] = resource['type']
            #employee['emp_rank'] = resource['rank']
            employee['emp_level'] = resource['emp_level']
            employee['emp_status'] = resource['emp_status']
            employee['emp_assigned'] = resource.get('emp_assigned', 0)
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
    command = 'grep -E ' + contract_id + ' -rl ' + baseURL + '/' + parentFolder + "/ > contract_data.txt"
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
            load_factor = get_load_factor(parentFolder, block, time)
            capacity = 0
            obj = {}
            files = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block)
            files.sort()

            #for file in files:
            file = files[len(files)-1]
            #print(file)
            path = baseURL + "/" + parentFolder + "/" + time + "/" + block + "/" + file
            data = read_json_from_file(path)
            resources = data["input"][0]["resources"]

            employees = []
            for resource in resources:
                #print(resource["emp_id"])
                employee = {}
                employee["emp_id"] = resource["emp_id"]
                employee["emp_assigned"] = resource.get('emp_assigned', 0)
                employee["warning"] = resource.get('warning', 0)
                employee["emp_type"] = resource["type"]
                capacity += employee["emp_assigned"]
                if employee not in employees:
                    employees.append(employee)
            #print(employees)
            employees.sort(key = lambda x : x["emp_assigned"], reverse = True)
            obj["block_id"] = data["input"][0]["block_id"]
            obj["block_name"] = data["input"][0]["block_name"]
            obj["block_center"] = data["input"][0]["block_center"]
            obj["block_distance"] = data["input"][0]["block_distance"]
            obj["employees"] = employees
            obj["capacity"] = "%.2f" % (capacity/float(len(employees)))
            obj["load_factor"] = load_factor
            result.append(obj)
            result.sort(key = lambda x: x['block_name'])
    except Exception as e:
        pass
    return json.dumps(result)

@app.route('/summary_old/<parentFolder>/<time>', methods = ['GET'])
def statistic_assigned_task_for_employee_bk(parentFolder, time):
    blocks = []
    requests = []
    try:
        command = 'grep -E "\\"assigned\\"\s*\:\s*\\"1\\"" -rl ' + baseURL + '/' + parentFolder + "/ > summary_blocks_data.txt"
        os.system(command)
        emp_dict = {}
        paths = []
        with open("summary_blocks_data.txt") as file:
            for line in file:
                paths.append(str(line).replace('\n', ''))
        paths.sort(reverse=True)

        for path in paths:
            backWardIdx = path.rfind('/')
            folderPath = path[0:backWardIdx]
            backWardIdx = folderPath.rfind('/')
            folderPath = folderPath[0:backWardIdx]
            folder_time = folderPath[-2:]
            #print(path)
            if int(folder_time) <= int(time):
                content = read_json_from_file(path)
                block_id = str(content["input"][0]["block_id"])
                #if block_id == "317516":
                # get all employees
                emps = []
                for emp_ in content["input"][0]["resources"]:
                    emp = {}
                    emp["emp_id"] = emp_["emp_id"]
                    emp["emp_type"] = emp_["type"]
                    emp["tasks"] = []
                    emp["emp_assigned"] = emp_['emp_assigned']
                    #print(emp)
                    if not any(e["emp_id"] == emp["emp_id"] for e in emps):
                        emps.append(emp)

                # update request done for emp
                #requests = []
                #print(len(emps))
                hcOutput = content["hc_output"]
                for hc in hcOutput:
                    rq = {}
                    if hc["assigned"] == "1":
                        #load_factor = hc["load_factor"]
                        rq["request_id"] = hc["request_id"]
                        rq["type"] = hc["type"]
                        if not any( str(r["request_id"]) == str(hc["request_id"]) and str(r["type"]) == str(hc["type"]) for r in requests):
                            #print(requests)
                            requests.append(rq)
                            for tmp_emp_id in emps:
                                file_name = path.strip().split("/")[5]
                                if tmp_emp_id["emp_id"] == hc["emp_id"] and not is_exists_request_id(file_name, hc["request_id"], parentFolder, block_id):
                                    if str(hc["request_id"]) not in tmp_emp_id["tasks"]:
                                        tmp_emp_id["tasks"].append(str(hc["request_id"]))
                                    break
                #print(len(emps))
                #print(emps)
                # get load_factor
                load_factor = get_load_factor(parentFolder, block_id, folder_time)

                if any(x["block_id"] == str(block_id) for x in blocks):
                    for b in blocks:
                        if b["block_id"] == str(block_id):
                            for new_emp in emps:
                                if not any(new_emp["emp_id"] == r["emp_id"] for r in b["employees"]):
                                    b["employees"].append(new_emp)
                                else:
                                    for old_emp in b["employees"]:
                                        for new_emp in emps:
                                            if old_emp["emp_id"] == new_emp["emp_id"]:
                                                old_emp["tasks"] = list(set(old_emp["tasks"] + new_emp["tasks"]))
                                                break
                else:
                    block = {}
                    block["block_id"] = str(block_id)
                    block["employees"] = emps
                    block["block_name"] = content["input"][0]["block_name"]
                    block["load_factor"] = load_factor
                    block["capacity"] = 0
                    blocks.append(block)

        blocks.sort(key = lambda x: x['block_id'])
        for b_ in blocks:
            capacity = 0
            for e_ in b_["employees"]:
                e_["emp_assigned"] = len(e_["tasks"])
                capacity += int(e_["emp_assigned"])
            b_["capacity"] = "%.2f" % (capacity/float(len(b_["employees"])))
            b_["employees"].sort(key = lambda x : x["emp_assigned"], reverse = True)

        blocks.sort(key = lambda x: x['block_name'])

    except Exception as e:
        raise e
    return json.dumps(blocks)

def get_load_factor(parentFolder, block_id, time):
    load_factor = 0
    try:
        filenames = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block_id)
        filenames.sort(reverse=True)
        filename = filenames[0]
        path = baseURL + "/" + parentFolder + "/" + time + "/" + block_id + "/" + filename
        data = read_json_from_file(path)
        hc_output_ = data['hc_output']
        if len(hc_output_) > 0:
            for hc in hc_output_:
                if hc["emp_id"] != "0":
                    load_factor = hc["load_factor"]
                    break
    except Exception as e:
        pass
    return load_factor

def count_assigned_task_emp(emp_id, parentFolder, block_id, time):
    command = 'grep -E "\\"assigned\\"\s*\:\s*\\"1\\"" -rl ' + baseURL + '/' + parentFolder + "/" + time + "/" + block_id + "/ > assigned_task_emp.txt"
    os.system(command)
    paths = []
    with open("assigned_task_emp.txt") as file:
        for line in file:
            paths.append(str(line).replace('\n', ''))
    paths.sort()
    result = []
    for path in paths:
        content = read_json_from_file(path)
        hcOutput = content["hc_output"]
        inputJs = content["input"][0]
        for hc in hcOutput:
            if int(hc["assigned"]) == 1:
                if hc["request_id"] in result:
                    result.remove(hc["request_id"])
                file_name = path.strip().split("/")[5]
                if hc["emp_id"] == emp_id and not is_exists_request_id(file_name, hc["request_id"], parentFolder, block_id):
                    result.append(hc["request_id"])

    return len(result)

@app.route('/map_block_time/<parentFolder>/<time>/<block_id>', methods = ['GET'])
def get_data_to_show_block_map(parentFolder, time, block_id):
    try:
        # show on map all employess that have assigned = 1 from first time zone to [time] "time"
        command = 'grep -E "\\"assigned\\"\s*\:\s*\\"1\\"" -rl ' + baseURL + '/' +  parentFolder + "/*/" + block_id + "/ > map_block_data.txt"
        os.system(command)
        emp_dict = {}
        paths = []
        with open("map_block_data.txt") as file:
            for line in file:
                paths.append(str(line).replace('\n', ''))
        paths.sort()
        for path in paths:
            #print(path)
            backWardIdx = path.rfind('/')
            folderPath = path[0:backWardIdx]
            backWardIdx = folderPath.rfind('/')
            folderPath = folderPath[0:backWardIdx]
            folder_time = folderPath[-2:]
            #print(folderPath)
            #print(folder_time)

            if int(folder_time) <= int(time):
                #print(folder_time)
                content = read_json_from_file(path)
                hcOutput = content["hc_output"]
                inputJs = content["input"][0]
                for hc in hcOutput:
                    if int(hc["assigned"]) == 1:
                        file_name = path.strip().split("/")[5]
                        if not is_exists_request_id(file_name, hc["request_id"], parentFolder, block_id):
                            obj = {}
                            obj["emp_id"] = hc["emp_id"]
                            obj["block_center"] = inputJs["block_center"]
                            obj["request_id"] = hc["request_id"]
                            obj["cus_coordinate"] = hc["cus_coordinate"]
                            obj["emp_distance"] = hc["emp_distance"]
                            if not is_exists_request_id_in_dict(str(obj["request_id"]), emp_dict):
                                if hc["emp_id"] in emp_dict:
                                    emp_dict[hc["emp_id"]].append(obj)
                                else:
                                    emp_dict[hc["emp_id"]] = [obj]

        result = []
        for v in emp_dict.values():
            result.append(v)
        #result.sort(key = lambda x: x["start_time"])
        return json.dumps(result)
    except Exception as ex:
        return json.dumps([])

def is_exists_request_id_in_dict(request_id, dict):
    for key, value in dict.iteritems():
        for request in value:
            if str(request ["request_id"]) == str(request_id):
                return True
    return False

@app.route('/maps/<parentFolder>/<block_id>/<emp_id>/<time>', methods = ['GET'])
def get_data_to_show_map(parentFolder, block_id, emp_id, time):
    command = 'grep -E "\\"assigned\\"\s*\:\s*\\"1\\"" -rl ' + baseURL + '/' +  parentFolder + "/*/" + block_id + "/ > map_data.txt"
    os.system(command)
    data = {}
    paths = []
    with open("map_data.txt") as file:
        for line in file:
            paths.append(str(line).replace('\n', ''))
    paths.sort()
    for path in paths:
        file_name = path.strip().split("/")[5]
        file_time = file_name.strip().split("_")[3][0:2]
        if int(file_time) > int(time):
            break
        content = read_json_from_file(path)
        hcOutput = content["hc_output"]
        inputJs = content["input"][0]
        tasks = inputJs["tasks"]
        resources = inputJs["resources"]
        for hc in hcOutput:
            if int(hc["assigned"]) == 1:
                if hc["request_id"] in data:
                    del data[hc["request_id"]]
                if hc["emp_id"] == emp_id and not is_exists_request_id(file_name, hc["request_id"], parentFolder, block_id):
                    obj = {}
                    obj["cus_coordinate"] = hc["cus_coordinate"]
                    obj["emp_distance"] = hc["emp_distance"]
                    obj["task_type"] = hc["type"]
                    obj["block_center"] = inputJs["block_center"]
                    obj["emp_coordinate"] = get_emp_coordinate(emp_id, resources)
                    obj["start_time"] = get_hour_and_minute_in_time(hc["start_time"])
                    obj["checkout_time"] = get_hour_and_minute_in_time(hc["checkout_time"])
                    tup = get_customer_level_by_request_id(tasks, hc["request_id"])
                    obj["appointmentdate"] = get_hour_and_minute_in_time(tup[4])
                    checkout_time = datetime.datetime.strptime(hc["checkout_time"], '%Y-%m-%d %H:%M:%S')
                    apdate = datetime.datetime.strptime(tup[4], '%Y-%m-%d %H:%M:%S')
                    obj["late_time"] = calculate_kpi_hen_fr_now(checkout_time, hc["type"], apdate, tup[8])
                    # print(obj["res_time"])
                    data[hc["request_id"]] = obj
    result = []
    for v in data.values():
        result.append(v)
    result.sort(key = lambda x: x["start_time"])
    return json.dumps(result)

@app.route('/lasttime/<parentFolder>', methods = ['GET'])
def get_last_time_log(parentFolder):
    latest_time = "000000"
    try:
        times = os.listdir(baseURL + "/" + parentFolder)
        time = max(times)
        blocks = os.listdir(baseURL + "/" + parentFolder + "/" + time)
        for block in blocks:
            filenames = os.listdir(baseURL + "/" + parentFolder + "/" + time + "/" + block)
            max_time_file = max(filenames)
            max_time = max_time_file.split("_")[3]
            if max_time > latest_time:
                latest_time = max_time
    except Exception as e:
        pass
    return json.dumps(latest_time)

@app.route('/emp_info/<parentFolder>/<emp_id>', methods=['GET'])
def get_emp_info(parentFolder, emp_id):
    result = {}
    try:
        command = 'grep -E "\\"emp_id\\"\s*\:\s*\\"' + emp_id.strip() + '\\"" -rl ' + baseURL + '/' +  parentFolder.strip() + "/*/*/* > emp_info_list.txt"
        os.system(command)
        emp_info_files = []
        with open("emp_info_list.txt") as file:
            for line in file:
                emp_info_files.append(str(line).replace('\n', ''))

        if len(emp_info_files) > 0:
            emp_info_files.sort(reverse=True)
            em_info_file = emp_info_files[0]
            # print(em_info_file)
            content = read_json_from_file(em_info_file)
            inputJs = content["input"][0]
            resources = inputJs["resources"]
            for rs in resources:
                if rs["emp_id"].strip().lower() == emp_id.strip().lower():
                    logemp = rs.get('logemp', '')
                    logemp = logemp.strip()
                    if not is_null_or_empty(logemp):
                        logemps = LogEmps(emp_id.strip(), logemp)
                        logemps.available = rs.get('available', '')
                        logemps.emp_coordinate = rs.get('emp_coordinate', '')
                        logemps.emp_status = rs.get('emp_status', '')
                        logemps.emp_task = rs.get('emp_task', '')
                        logemps.performance = rs.get('performance', '')
                        logemps.request_impossible = rs.get('request_impossible', '')
                        logemps.type = rs.get('type', '')
                        logemps.emp_level = rs.get('emp_level', '')
                        logemps.block_id = inputJs.get('block_id','')
                        logemps.block_name = inputJs.get('block_name', '')
                        logemps.res_time = inputJs.get('res_time', '')

                        logemps.parser()
                        logemps.log_emps.sort(key=lambda x: x.event_date_time)
                        # print(len(logemps.log_emps))
                        result = logemps.make_json()
                    break
        pass
    except Exception as e:
        pass
    return result


def get_emp_coordinate(emp_id, resources):
    for resource in resources:
        if resource["emp_id"] == emp_id:
            return resource["emp_coordinate"]
    return "0,0"

def is_exists_request_id(file_name, request_id, parentFolder, block_id):
    command = 'grep -E "\\"request_id\\"\s*\:\s*\\"' + request_id + '\\"" -rl ' + baseURL + '/' +  parentFolder + "/*/" + block_id + "/ > request_id_file.txt"
    os.system(command)
    request_id_file = []
    with open("request_id_file.txt") as file:
        for line in file:
            request_id_file.append(str(line).replace('\n', ''))
    request_id_file.sort()
    for file in request_id_file:
        file1 = file.strip().split("/")[5]
        if get_time_from_file_name(file1) > get_time_from_file_name(file_name):
            command1 = 'grep -E "\\"assigned\\"\s*\:\s*\\"2\\"" -r ' + file + " > assigned2.txt"
            os.system(command1)
            if os.stat("assigned2.txt").st_size > 0:
                return True
    return False


def get_time_from_file_name(file_name):
    return file_name.strip().split(".")[0].split("_")[3]

def get_hour_and_minute_in_time(custom_time):
    tmp = custom_time.strip().split(" ")[1]
    return tmp[0:5]

def calculate_kpi_hen_fr_now(_res_time, task_task_type, task_appointment_date, task_date_confirmed):
    # type: (datetime, object, datetime, datetime) -> object
    appointmentdate = task_appointment_date

    m = task_appointment_date.minute
    if 5 <= m <= 25 or 35 <= m <= 55: # hen khung gio le
        if task_task_type == 1:
            appointmentdate = task_appointment_date + datetime.timedelta(hours=2.0 - m / 60.)
        else:
            appointmentdate = task_appointment_date + datetime.timedelta(hours=1.0 - m / 60.)

    if task_task_type == 1:
        if task_date_confirmed == 0:
            kpi_date = appointmentdate + datetime.timedelta(hours=48)
        else:
            kpi_date = appointmentdate + datetime.timedelta(hours=1.5)
    else:

        if task_date_confirmed == 0:
            kpi_date = appointmentdate + datetime.timedelta(hours=2)
        else:
            kpi_date = appointmentdate + datetime.timedelta(hours=1)

    dt = kpi_date - _res_time
    kpi_hen_fr_now = dt.days * 24 * 60 + dt.seconds // 60  # the number of minutes
    return kpi_hen_fr_now

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