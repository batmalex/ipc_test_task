import json
import logging
import os, sys
from time import sleep
from multiprocessing.connection import Client


PATH_TO_FILE = os.environ.get("PATH_TO_FILE", "resources/access_points.json")
TIMEOUT_TO_FETCH_SECONDS = os.environ.get("TIMEOUT_TO_FETCH_SECONDS", 1)
TIMEOUT_TO_RECONNECT_SECONDS = os.environ.get("TIMEOUT_TO_RECONNECT_SECONDS", 5)
MAX_RETRIES = os.environ.get("MAX_RETRIES", 5)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
CONNECTION_HOST = os.environ.get("CONNECTION_HOST", '0.0.0.0')
CONNECTION_PORT = os.environ.get("CONNECTION_PORT", 5555)
CONNECTION_AUTH_KEY = os.environ.get("CONNECTION_AUTH_KEY", b'password')


logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s r%(message)s')


def read_data(path_to_file):
    """
    Reads the input file with AP's data
    :param path_to_file:
    :return:
    """
    with open(path_to_file, "r") as f:
        access_points = json.loads(f.read())
    return access_points


def main():
    if os.path.exists(PATH_TO_FILE):
        last_update = os.stat(PATH_TO_FILE).st_mtime
    else:
        logging.warning(msg="Source file not found. Please check out the path")
        sys.exit(1)

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            with Client((CONNECTION_HOST, CONNECTION_PORT), authkey=CONNECTION_AUTH_KEY) as conn:
                last_sent = last_update - 1

                while True:
                    if last_update > last_sent:
                        income_aps = read_data(path_to_file=PATH_TO_FILE)
                        logging.debug(msg=f"Read data from file {income_aps}")
                        conn.send(income_aps)
                        last_sent = last_update
                    sleep(TIMEOUT_TO_FETCH_SECONDS)
                    last_update = os.stat(PATH_TO_FILE).st_mtime

        except ConnectionError as err:
            logging.error(msg=f"Connection failed because {err.args}.\nTrying to reconnect to the server...")
            attempt += 1
            sleep(TIMEOUT_TO_RECONNECT_SECONDS)

        except OSError as err:
            logging.error(msg=f"Something went wrong {err.args}.\nTrying to reconnect to the server...")
            attempt += 1
            sleep(TIMEOUT_TO_RECONNECT_SECONDS)


if __name__ == "__main__":
    main()
