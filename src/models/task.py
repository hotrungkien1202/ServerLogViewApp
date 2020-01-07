class Task:
    def __init__(self, request_id, type, sub_type_1, sub_type_2, reason_out_case, appointmentdate, manual_priority, emp_speciallized, contract, date_confirmed, appointmentdate2, is_camera_taks, time_zone):
        self.request_id = request_id
        self.type = type
        self.sub_type_1 = sub_type_1
        self.sub_type_2 = sub_type_2
        self.reason_out_case = reason_out_case
        self.appointmentdate = appointmentdate
        self.manual_priority = manual_priority
        self.emp_speciallized = emp_speciallized
        self.contract = contract
        self.date_confirmed = date_confirmed
        self.appointmentdate2 = appointmentdate2
        self.is_camera_taks = is_camera_taks
        self.time_zone = time_zone


class AssignedTask(Task):
    def __init__(self,request_id, type, sub_type_1, sub_type_2, reason_out_case, appointmentdate, manual_priority, emp_speciallized, contract, date_confirmed, start_time, checkin_time, checkout_time, priority, late_time, assigned, appointmentdate2, is_camera_taks, time_zone):
        self.start_time = start_time
        self.checkin_time = checkin_time
        self.checkout_time  = checkout_time
        self.priority = priority
        self.late_time = late_time
        self.assigned = assigned
        Task.__init__(self, request_id, type, sub_type_1, sub_type_2, reason_out_case, appointmentdate, manual_priority, emp_speciallized, contract, date_confirmed, appointmentdate2, is_camera_taks, time_zone)


