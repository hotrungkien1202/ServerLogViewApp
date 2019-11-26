from common.utils import *
import os

def parser_special_date_time_str(str_d_time_):
    double_dot_pos = str_d_time_.strip().index(':')
    rs = str_d_time_.strip()[(double_dot_pos + 1):]
    return rs


def get_event(event_str):
    if str(event_str) == Events.ASSIGNED_TASK['code']:
        return Events.ASSIGNED_TASK['desc']
    elif str(event_str) == Events.ACCEPT_TASK['code']:
        return Events.ACCEPT_TASK['desc']
    elif str(event_str) == Events.OUT_CASE['code']:
        return Events.OUT_CASE['desc']
    elif str(event_str) == Events.CHECK_IN['code']:
        return Events.CHECK_IN['desc']
    elif str(event_str) == Events.MORNITORING['code']:
        return Events.MORNITORING['desc']
    elif str(event_str) == Events.CHECK_OUT['code']:
        return Events.CHECK_OUT['desc']
    elif str(event_str) == Events.RE_CALL['code']:
        return Events.RE_CALL['desc']
    return None, None


class Events:
    # 1: Phan tuyen
    # 2: Nhan Tuyen
    # 3: Nha tuyen
    # 4: Check in
    # 5: Da xu ly, dang theo doi
    # 6: Checkout (hoan tat)
    # 7: Recall
    ASSIGNED_TASK = {'code': '1', 'desc': 'Assigned task'}
    ACCEPT_TASK = {'code': '2', 'desc': 'Accepted task'}
    OUT_CASE = {'code': '3', 'desc': 'Rejected task'}
    CHECK_IN = {'code': '4', 'desc': 'Check in'}
    MORNITORING = {'code': '5', 'desc': 'Monitoring'}
    CHECK_OUT = {'code': '6', 'desc': 'Check out'}
    RE_CALL = {'code': '7', 'desc': 'Re-call'}


class LogEmp:

    def __init__(self, emp_id, request_id, request_type, event_code, event_desc, event_date_time):
        # type: (str, str, str, str, str, str) -> None
        self.emp_id = emp_id
        self.request_id = request_id
        self.request_type = request_type
        self.event_code = event_code
        self.event_desc = event_desc
        self.event_date_time = event_date_time

    def get_request_info(self):
        pass


class LogEmps:
    def __init__(self, emp_id, str_log_elm, available=None, emp_coordinate=None, emp_level=None, emp_status=None,
                 emp_task=None, performance=None, request_impossible=None, type=None, block_id=None, res_time=None,
                 block_name=None):
        self.emp_id = emp_id
        self.str_log_elm = str_log_elm
        self.available = available
        self.emp_coordinate = emp_coordinate
        self.emp_level = emp_level
        self.emp_status = emp_status
        self.emp_task = emp_task
        self.performance = performance
        self.request_impossible = request_impossible
        self.type = type
        self.block_id = block_id
        self.block_name = block_name
        self.res_time = res_time

        self.log_emps = []

    def make_json(self, baseURL, parentFolder):
        return {
            "emp_id": str(self.emp_id),
            "block_id": str(self.block_id),
            "block_name": str(self.block_name),
            "res_time": str(self.res_time),
            "available": str(self.available),
            "emp_coordinate": str(self.emp_coordinate),
            "emp_level": str(self.emp_level),
            "emp_status": str(self.emp_status),
            "emp_task": str(self.emp_task),
            "performance": self.performance,
            "request_impossible": str(self.request_impossible),
            "type": str(self.type),
            "event_logs": self.__make_log_list_json(baseURL, parentFolder)
        }

    def __make_log_list_json(self, baseURL, parentFolder):
        rs = []
        for log in self.log_emps:  # type: LogEmp
            rs.append({
                "request": self.get_latest_request_info(baseURL, log.request_id, log.request_type, parentFolder),
                "event_code": log.event_code,
                "event_desc": log.event_desc,
                "event_date_time": str(log.event_date_time)
            })
        return rs

    def get_latest_request_info(self, baseURL, request_id, request_type, parentFolder):
        # type: (str, str, str) -> object
        result = {}
        try:
            command = 'grep -E "\\"request_id\\"\s*\:\s*' + request_id.strip() + '" -rl ' + baseURL + '/' + parentFolder.strip() + "/*/*/* > request_info_list.txt"
            os.system(command)
            rq_info_files = []
            with open("request_info_list.txt") as file:
                for line in file:
                    rq_info_files.append(str(line).replace('\n', ''))

            if len(rq_info_files) > 0:
                rq_info_files.sort(reverse=True)
                rq_info_files = rq_info_files[0]
                # print(em_info_file)
                content = read_json_from_file(rq_info_files)
                inputJs = content["input"][0]
                tasks = inputJs["tasks"]
                for task in tasks:
                    if str(task["request_id"]).strip().lower() == request_id.strip().lower() \
                            and str(task["type"]).strip().lower() == request_type.strip().lower():
                        result = task
                        break
        except Exception as e:
            pass
        if len(result) == 0:
            result = {
                "request_id": request_id,
                "contract": "N/A",
                "type": request_type
            }
        return result

    def parser(self):
        # print("parser log emp ==========================")
        if not is_null_or_empty(self.str_log_elm):
            elms = self.str_log_elm.strip().split(';')
            for elm in elms:
                if not is_null_or_empty(elm):
                    request_id, request_type, event_code, event_desc, event_date_time = self.__parser_log_item(
                        elm.strip())
                    log = LogEmp(self.emp_id, request_id, request_type, event_code, event_desc, event_date_time)
                    # check log is in list
                    is_existed_in_log = False
                    # print ("log.request_id, log.request_type, log.event_code: %s, %s, %s" % (log.request_id, log.request_type, log.event_code))
                    for tmp_log in self.log_emps:
                        if log.request_id == tmp_log.request_id and log.request_type == tmp_log.request_type and log.event_code == tmp_log.event_code:
                            is_existed_in_log = True
                            tmp_log.emp_id = log.emp_id
                            tmp_log.request_id = log.request_id
                            tmp_log.request_type = log.request_type
                            tmp_log.event_code = log.event_code
                            tmp_log.event_desc = log.event_desc
                            tmp_log.event_date_time = log.event_date_time
                            break
                    if not is_existed_in_log:
                        self.log_emps.append(log)
        pass

    def __parser_log_item(self, str_log_item):
        request_id = None
        request_type = None
        event_code = None
        event_desc = None
        event_date = None
        if not is_null_or_empty(str_log_item):
            elms = str_log_item.strip().split(',')
            if len(elms) == 2:
                str_code = elms[0]
                str_date = elms[1]
                request_id, request_type, event_code, event_desc = self.__parse_code(str_code)
                event_date = self.__parse_date(str_date)
        return request_id, request_type, event_code, event_desc, event_date

    def __parse_date(self, str_date):
        ev_date = None
        try:
            if not is_null_or_empty(str_date):
                ev_date = to_date_time(parser_special_date_time_str(str_date))
        except Exception as ex:
            pass
        return ev_date

    def __parse_code(self, str_code):
        request_id = None
        request_type = None
        event_code = None
        event_desc = None
        if not is_null_or_empty(str_code):
            elms = str_code.strip().split(':')
            if len(elms) == 2:
                str_rqs = elms[0].strip().split('_')
                if len(str_rqs) == 3:
                    request_id = str_rqs[0].strip()
                    request_type = str_rqs[1].strip()
                    event_code = elms[1].strip()
                    event_desc = get_event(event_code)
        return request_id, request_type, event_code, event_desc
