let _command_queue = [];
let _response_inx = 0;
let _tcl_buffer = "";
let _tcl_last_save = "";

let _log_buffer = "";
let _log_offset = 0;

let _tcl_title = "----------";
let _tcl_version = "--";

let _page_dirty = false;

const _command_prefix = ">";

function render() {
    buffr = "";
    let i;
    for (i = Math.max(_command_queue.length - 10, 0); i < _command_queue.length; i++) {
        buffr = buffr + _command_queue[i];
        if (i < _command_queue.length - 1) {
            buffr += '\n';
        }
    }
    $('#command_win').val(buffr);

    if (_tcl_title != null) {
        $('#tcl_title').html(_tcl_title);
        _tcl_title = null;
    }

    if (_tcl_version != null) {
        $('#tcl_version').html(_tcl_version);
        _tcl_version = null;
    }

    if (_tcl_buffer != null) {
        $('#tcl_text').val(_tcl_buffer);
        _tcl_buffer = null;
    }

    if (_tcl_last_save != $('#tcl_text').val()) {
        $("#tcl_title").css("color", "red");
        $("#tcl_version").css("color", "red");
    } else {
        $("#tcl_title").css("color", "blue");
        $("#tcl_version").css("color", "blue");
    }
}

function updateLog() {
    $.ajax({
        type: 'Get',
        url: server_url + 'log',
        data: {
            offset: _log_offset.toString()
        },
        success: function (data) {
            let ret = JSON.parse(data);
            for (let i = 0; i < ret.rows.length; i++) {
                let row = ret.rows[i];
                //row = JSON.parse(r);
                d = row.asctime.substring(11, 19);
                l = row.levelname.substring(0, 1);
                _log_buffer += `<span style="color:Blue;">${l} | ${d} | ${row.url} -- </span>  ${row.message} <br>`;
                _log_offset += 1;
            }
            renderLog();
        }
    });
}

function renderLog() {
    $('#log_text').html(_log_buffer);
}

function new_command_line() {
    _command_queue.push(_command_prefix);
    _recall_index = _command_queue.length - 1;
}

function handle_command_return(data) {
    let ret = JSON.parse(data);
    if (ret.type == "message") {
        _command_queue[_response_inx] = `   [${ret.sender}]: ${ret.message}`;
    }
    else {
        _command_queue[_response_inx] = `   [${ret.sender}]: ${ret.message}`;
        _tcl_buffer = ret.code;
        _tcl_last_save = _tcl_buffer;
        _tcl_title = `${ret.filename}`;
        _tcl_version = `v[${ret.version}]`;
    }
    _page_dirty = true;
}

// sends a command to the esp server
function post_command(command_text) {
    // create line for response in command window.
    _command_queue.push("");
    _response_inx = _command_queue.length - 1;
    new_command_line();

    $.ajax({
        type: "POST",
        url: server_url + 'command',
        data: {
            command: command_text,
            tcl: $('#tcl_text').val()
        },
        success: function (data) {
            handle_command_return(data);
        },
        error: function (jqXHR, text, error) {
            _command_queue[_response_inx] = `  [0]: Error -- ${error}`;
            _page_dirty = true;
        }
    });
}

function process_key(keyCode, keyChar) {
    let current_line = _command_queue[_command_queue.length - 1];
    switch (keyCode) {
        // CR
        case 13: {
            console.log("Handler for .keypressdfs() called.");
            let command_text = current_line.substring(_command_prefix.length, current_line.length);
            post_command(command_text);
            return;
        }
        // backspace{
        case 8: {
            if (current_line.length > _command_prefix.length) {
                current_line = current_line.substring(0, current_line.length - 1);
            }
            break;
        }
        // shift... right now everything is lc
        case 16:
        case 20: {
            break;
        }
        // arrow up
        case 38: {
            while (_recall_index > 0) {
                _recall_index -= 1;
                new_line = _command_queue[_recall_index];
                if (new_line != current_line && new_line[0] == _command_prefix) {
                    current_line = new_line;
                    break;
                }
            }
            break;
        }
        // arrow down
        case 40: {
            while (_recall_index < _command_queue.length - 1) {
                _recall_index += 1;
                new_line = _command_queue[_recall_index];
                if (new_line != current_line && new_line[0] == _command_prefix) {
                    current_line = new_line;
                    break;
                }
            }
            break;
        }
        default: {
            current_line = current_line + keyChar;
            break;
        }
    }
    _command_queue[_command_queue.length - 1] = current_line;
    _page_dirty = true;
}

// Any key in the command window
$('#command_win').keydown(function (e) {
    e.preventDefault();
    process_key(e.keyCode, e.key);
});

// A change in the text window
$('#tcl_text').keydown(function (e) {
    _page_dirty = true;
});

// Run button
$("#run_button").click(function () {
    post_command("run");
});

// Save button
$("#save_button").click(function () {
    post_command("save");
});

// Clear log panel
$("#clear_log_button").click(function () {
    _log_buffer = "";
    renderLog()
});

// ---------------------------------------------
// Timekeeper...
// ---------------------------------------------

let _last_time = 0;
let _log_time = 0;

function delta_time() {
    let _date_time = new Date();
    _current_time = _date_time.getTime();
    let delta = _current_time - _last_time;
    _last_time = _current_time;
    return delta;
}

// refresh page when dirty...
function update(timestamp) {
    if (_page_dirty) {
        render();
        _page_dirty = false;
    }

    _log_time += delta_time();
    if (_log_time > 1500) {
        _log_time = 0;
        updateLog();
    }

    window.requestAnimationFrame(update)
}


// first line...
delta_time();
new_command_line();
render();
update(0);
