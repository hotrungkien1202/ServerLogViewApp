import datetime
import json


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def json_default(value):
    if isinstance(value, datetime.date):
        return str(value)
    else:
        return value.__dict__

def read_json_from_file(path):
    try:
        with open(path) as json_file:
            return json.load(json_file)
    except Exception as e:
        raise e

def is_none(v):
    if v is None:
        return True
    return False


def is_empty(_str):
    if isinstance(_str, basestring):
        return is_none(_str) or len(_str.strip()) == 0
    return False


def is_null_or_empty(_str):
    if is_none(_str):
        return True
    if isinstance(_str, basestring):
        if is_empty(_str):
            return True
        if len(_str.strip()) > 0:
            return _str.strip().isspace()
        return True
    return False


def to_date_time(str):
    datetime_object = datetime.datetime.strptime(str, DATETIME_FORMAT)
    return datetime_object
