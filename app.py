from flask import Flask
from flask import render_template
from flask import request, json

from Command import CommandParser
from ESPManager import esp_manager
from Logging import jlog
from tasks import Backgrounder

app = Flask(__name__)
cmd = CommandParser()


@app.route('/')
def index():
    return render_template('control_panel.html', title='ESP8266 Server', server_url=request.url_root)


# endpoint for commands from control panel
@app.route('/command', methods=['POST'])
def command():
    c = request.form['command']
    ret = cmd.parse(request.form['command'], request.form['tcl'])
    ret["sender"] = 0
    ret = json.dumps(ret)
    # jlog.flask_request(request, request.form['command'], ret)
    return ret


# endpoint for connection information from each esp device
@app.route('/connect')
def connect():
    url = request.remote_addr
    ret = esp_manager.handle_connection(url)
    ret = json.dumps(ret)
    return ret


@app.route('/post_log', methods=['POST'])
def post_log():
    r = request
    print(r.json)
    jlog.event(request.json['levelname'], request.json["message"], request.remote_addr)
    return ""


# request to get log.  Returns rows of logs...
@app.route('/log')
def log():
    off = int(request.args.get('offset'))
    rows = jlog.rows(off)
    ret = {"rows": rows}
    return json.dumps(ret)


def update():
    esp_manager.update()


if __name__ == '__main__':
    # kick up background task.
    bgrnd = Backgrounder()
    bgrnd.start_worker(update, 1)
    # reloader reloads this module for debug purposes...
    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0')
else:
    # kick up background task.
    bgrnd = Backgrounder()
    bgrnd.start_worker(update, 1)
