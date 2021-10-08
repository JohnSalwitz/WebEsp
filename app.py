from flask import Flask
from flask import render_template
from flask import request, json

from Command import CommandParser
from Logging import jlog
from tasks import Backgrounder
from mqq_handler import mqq_handler
from ESPManager import esp_manager

app = Flask(__name__)
cmd = CommandParser()

_start_message = "Hello From ESP Server"

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

@app.route('/post_log', methods=['POST'])
def post_log():
    jlog.event(request.json['levelname'], request.json["message"], request.remote_addr)
    return ""

# request to get log.  Returns rows of logs...
@app.route('/log')
def log():
    off = int(request.args.get('offset'))
    rows = jlog.rows(off)
    ret = {"rows": rows}
    return json.dumps(ret)

# push mqq log message into log q.
def log_message_handler(client, obj, msg):
    print("ON MESSAGE: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    log_data = json.loads(msg.payload)
    jlog.event(log_data['levelname'], log_data["message"], log_data["client"])

if __name__ == '__main__':

    # setup cloud mqqt
    mqq_handler.init("esp monitor")
    mqq_handler.add_callback("esp/log", log_message_handler)
    mqq_handler.publish("esp/log", _start_message)

    esp_manager.init()

    # reloader reloads this module for debug purposes...
    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0')
