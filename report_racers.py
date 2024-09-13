from pathlib import Path
from datetime import datetime
from datetime import timedelta

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ABBR_FILE = DATA_DIR / "abbreviations.txt"
STARTLOG_FILE = DATA_DIR / "start.log"
ENDLOG_FILE = DATA_DIR / "end.log"
DATETIME_FORMAT = '%Y-%m-%d_%H:%M:%S.%f'
STRTIME_FORMAT = '%M:%S.%f'
TOP_DELIMITER = 15


def read_data_file(file_path: Path) -> list:
    """This function reads data from files located in the data folder,
         called for files of race times and abbreviations of racers"""
    with open(file_path, 'r') as fp:
        content = fp.read().split('\n')
        return content


def parse_race_file(file: Path) -> dict[str, datetime]:
    """This function parses race data from a file. returns a dictionary,
         where the key is the racer's initials and the value is the time"""
    race_data = dict()
    result_time = read_data_file(file)
    for line in result_time:
        if not line:
            break
        driver = line[:3].strip()
        date_time = line[3:].strip()
        date_time = datetime.strptime(date_time, DATETIME_FORMAT)
        race_data[driver] = date_time
    return race_data


def parser_drivers(file: Path) -> dict[str, list]:
    """This function parses data about riders from a file. returns a dictionary in which
         the key is the driver's initials and the value is the driver's name and team name"""
    drivers_data = dict()
    result_abbr = read_data_file(file)
    for line in result_abbr:
        if not line:
            break
        list_abbr = line.strip().split('_')
        drivers_data[list_abbr[0]] = list_abbr[1:]
    return drivers_data


def build_report(order):
    start = parse_race_file(STARTLOG_FILE)
    end = parse_race_file(ENDLOG_FILE)
    abbr = parser_drivers(ABBR_FILE)
    result = dict()
    zero_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for name, st_time in start.items():
        if st_time > end[name]:
            st_time, end[name] = end[name], st_time
        time_difference = (
            zero_time + (end[name] - st_time)).strftime(STRTIME_FORMAT)
        result[str(time_difference)] = name, *abbr[name]
        if order == 'desc':
            result = dict(reversed(result.items()))
    return result


def get_racer_data(report: dict[str, tuple], name: str):
    racer_data = dict(filter(lambda item: name in item[1], report.items()))
    return racer_data
