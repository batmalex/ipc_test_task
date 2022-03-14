from multiprocessing.connection import Listener
from datetime import datetime
from time import sleep
import logging
import os
from web_app import app_chart


TIMEOUT_SECONDS = 1
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
CONNECTION_HOST = os.environ.get("CONNECTION_HOST", '0.0.0.0')
CONNECTION_PORT = os.environ.get("CONNECTION_PORT", 5555)
CONNECTION_AUTH_KEY = os.environ.get("CONNECTION_AUTH_KEY", b'password')
PATH_TO_OUTPUT = os.environ.get("PATH_TO_OUTPUT", './output_data/')
MAX_CONNECTION_RETRIES = os.environ.get("MAX_CONNECTION_RETRIES", 5)
WEB_APP_HOST = os.environ.get("WEB_APP_HOST", '0.0.0.0')
WEB_APP_PORT = os.environ.get("WEB_APP_PORT", '85')
WEB_APP_DEBUG_MODE = os.environ.get("WEB_APP_DEBUG_MODE", False)
WEB_APP_RELOADER = os.environ.get("WEB_APP_RELOADER", False)

current_aps = {}
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s r%(message)s')


def compare_objects(income):
    """
    The function compares two json objects of the state of the AP's - current and another one that was get from the file
    after the changes.
    Use the subtraction of the sets that are creating from the dict's keys
    :param income:
    :return:
    """

    global current_aps
    current = current_aps

    if isinstance(income, dict):
        income = {v.get('ssid'): v for v in income.get('access_points')}
    else:
        logging.error(msg=f"Received bad format of json object. {income}")
        return []

    current_keys = {k for k in current}
    income_keys = {k for k in income}
    matched_keys = current_keys & income_keys

    added_aps = {k: v for k, v in income.items() if k not in current}
    removed_aps = {k: v for k, v in current.items() if k not in income}
    changed_aps = {}
    for k in matched_keys:
        changed_aps[k] = {}
        if (old := current.get(k).get('snr')) != (new := income.get(k).get('snr')):
            changed_aps[k]['snr'] = [old, new]

        if (old := current.get(k).get('channel')) != (new := income.get(k).get('channel')):
            changed_aps[k]['channel'] = [old, new]

    current_aps = income

    return [added_aps, removed_aps, changed_aps]


def write_report(diffs):
    """
    The function writes the result of changing of the input-file to the log-file
    :param diffs:
    :return:
    """
    output_file = os.path.join(PATH_TO_OUTPUT, datetime.today().strftime('%Y-%m-%d'))
    with open(output_file, 'a') as f:
        if added_aps := diffs[0]:
            for k, v in added_aps.items():
                f.write(f"{k} is added to the list with SNR {v.get('snr')} and channel {v.get('channel')}\n")

        if removed_aps := diffs[1]:
            for k in removed_aps.keys():
                f.write(f"{k} is removed from the list\n")

        if changed_aps := diffs[2]:
            for k, v in changed_aps.items():
                data = ""
                key_exists = False
                if change_interval := v.get('snr'):
                    data = f"SNR value has changed from {change_interval[0]} to {change_interval[1]}"
                    key_exists = True

                if change_interval := v.get('channel'):
                    if key_exists:
                        data += " and "
                    data += f"channel value has changed from {change_interval[0]} to {change_interval[1]}"
                    key_exists = True

                if key_exists:
                    f.write(f"{k}'s {data}\n")


def start_web_app():
    """
    Runs in a separate thread Flask application with a chart bar
    :return:
    """
    app_chart.run_web_app(host=WEB_APP_HOST, port=WEB_APP_PORT, debug=WEB_APP_DEBUG_MODE, reloader=WEB_APP_RELOADER)


def update_web_chart(data):
    """
    Updates the bar charts in the web-app application
    :param data:
    :return:
    """
    app_chart.update_chart(data=data)


def main():
    start_web_app()

    try:
        with Listener((CONNECTION_HOST, CONNECTION_PORT), authkey=CONNECTION_AUTH_KEY) as listener:
            attempt = 0
            while attempt < MAX_CONNECTION_RETRIES:
                try:
                    conn = listener.accept()
                    logging.info(msg=f"Socket connection accepted from the {listener.last_accepted}")
                    attempt = 0
                    while True:
                        message = conn.recv()
                        if diff_objects := compare_objects(income=message):
                            update_web_chart(data=message)
                            write_report(diff_objects)

                except ConnectionError or EOFError as err:
                    conn.close()
                    logging.error(msg=f"Something went wrong with connection {err.args}\nTrying to restart connection.")
                    attempt += 1
                    sleep(TIMEOUT_SECONDS)

    except KeyboardInterrupt as err:
        if listener:
            listener.close()
        logging.warning(msg="The server has been stopped by Keyboard interruption command")


if __name__ == "__main__":
    main()