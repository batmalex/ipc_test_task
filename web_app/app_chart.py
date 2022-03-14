from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Lock, Thread
import logging, os


WEB_APP_HOST = os.environ.get("WEB_APP_HOST", '0.0.0.0')
WEB_APP_PORT = os.environ.get("WEB_APP_PORT", '85')
WEB_APP_DEBUG_MODE = os.environ.get("WEB_APP_DEBUG_MODE", False)
WEB_APP_RELOADER = os.environ.get("WEB_APP_RELOADER", False)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s r%(message)s')
async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socket = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


@app.route('/')
def index():
    labels = []
    values = []
    return render_template('bar_chart.html', title='Wireless data bar', labels=labels,
                           values=values, sync_mode=socket.async_mode)


def update_chart(data):
    socket.emit('update_chart', data)
    logging.debug(msg=f"Updated bar chart with data {data}")


def run_web_app(host=WEB_APP_HOST, port=WEB_APP_PORT, debug=WEB_APP_DEBUG_MODE, reloader=WEB_APP_RELOADER):
    logging.info(msg=f"Web application started with socket {socket}")
    Thread(target=lambda: socket.run(app, host=host, port=port, debug=debug, use_reloader=reloader)).start()


if __name__ == '__main__':
    run_web_app()
