class Task:
    def __init__(self, request_id, type, sub_type_1, sub_type_2, reason_out_case, appointmentdate, manual_priority, emp_speciallized):
        self.request_id = request_id
        self.type = type
        self.sub_type_1 = sub_type_1
        self.sub_type_2 = sub_type_2
        self.reason_out_case = reason_out_case
        self.appointmentdate = appointmentdate
        self.manual_priority = manual_priority
        self.emp_speciallized = emp_speciallized


class AssignedTask(Task):
    def __init__(self,request_id, type, sub_type_1, sub_type_2, reason_out_case, appointmentdate, manual_priority, emp_speciallized, start_time, checkin_time, checkout_time, priority, late_time, assigned):
        self.start_time = start_time
        self.checkin_time = checkin_time
        self.checkout_time  = checkout_time
        self.priority = priority
        self.late_time = late_time
        self.assigned = assigned
        Task.__init__(self, request_id, type, sub_type_1, sub_type_2, reason_out_case, appointmentdate, manual_priority, emp_speciallized)


