from flask import Flask
from flask import render_template
from flask import request, json
from Command import CommandParser

from tasks import Backgrounder

app = Flask(__name__)
cmd = CommandParser()

_control_block = {"status" : 0}

@app.route('/')
def index():
    return render_template('signup.html', title='ESP8266 Server')

@app.route('/command', methods=['POST'])
def command():
    ret = cmd.parse(request.form['command'], request.form['tcl'])
    ret["sender"] = 0
    ret = json.dumps(ret)
    return ret

@app.route('/ttt')
def ttt():
    #print(json.dumps(_control_block))
    return json.dumps(_control_block)

@app.route('/on')
def on():
    _control_block["status"] = 1
    return "Relay is On"

@app.route('/off')
def off():
    _control_block["status"] = 0
    return "Relay is Off"

def mytask():
    _control_block["status"] = 1 - _control_block["status"]
    pass


if __name__=="__main__":
    app.run()

if __name__ == '__main__':
    # stops flask from reloading twice
    # kick up background task.
    bgrnd = Backgrounder()
    bgrnd.start_worker(mytask, 10)
    # reloader reloads this module for debug purposes...
    app.run(debug=False, use_reloader=False, threaded=True, host='0.0.0.0')