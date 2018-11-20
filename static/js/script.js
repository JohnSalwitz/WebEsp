
let _command_queue = [];
let _response_inx = 0;
let _tcl_buffer = "";
let _tcl_last_save = ""

let _tcl_title = "----------";
let _tcl_version = "--";

let _page_dirty = false;

const _command_prefix = ">";

function new_command_line() {
    _command_queue.push(_command_prefix);
    _recall_index = _command_queue.length - 1;
}

function handle_command_return(data) {
    let ret = JSON.parse(data);
    if(ret.type == "message") {
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


function render() {
    buffr = "";
    let i;
    for(i = Math.max(_command_queue.length-10, 0); i < _command_queue.length; i++) {
        buffr = buffr + _command_queue[i];
        if(i < _command_queue.length-1) {
            buffr += '\n';
        }
    }
    $('#command_win').val(buffr);

    if(_tcl_title != null) {
        $('#tcl_title').html(_tcl_title);
        _tcl_title = null;
    }

     if(_tcl_version != null) {
        $('#tcl_version').html(_tcl_version);
        _tcl_version = null;
    }

    if(_tcl_buffer != null) {
        $('#tcl_text').val(_tcl_buffer);
        _tcl_buffer = null;
    }

    if(_tcl_last_save != $('#tcl_text').val()) {
        $("#tcl_title").css("color", "red");
        $("#tcl_version").css("color", "red");
    } else{
        $("#tcl_title").css("color", "blue");
        $("#tcl_version").css("color", "blue");
    }

}

function process_key(keyCode, keyChar){
    let current_line = _command_queue[_command_queue.length - 1];
    switch(keyCode) {
        // CR
        case 13: {
            console.log( "Handler for .keypressdfs() called." );

            // create line for response
            _command_queue.push("");
            _response_inx = _command_queue.length-1;
            new_command_line();

            $.ajax({
                type: "POST",
                url: 'http://127.0.0.1:5000/command',
                data: {
                    command:  current_line.substring(_command_prefix.length, current_line.length),
                    tcl : $('#tcl_text').val()},
                success: function (data) {
                    handle_command_return(data);
                },
                error: function (jqXHR, text, error) {
                    _command_queue[_response_inx] = `  [0]: Error -- ${error}`;
                    _page_dirty = true;
                }
            });
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
            while(_recall_index > 0) {
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
        default:{
            current_line = current_line + keyChar;
            break;
        }
    }
    _command_queue[_command_queue.length - 1] = current_line;
    _page_dirty = true;
}

$('#command_win').keydown(function(e) {
    e.preventDefault();
    process_key(e.keyCode, e.key);
});

$('#tcl_text').keydown(function(e) {
    _page_dirty = true;
});

// refresh page when dirty...
function update(timestamp) {
    if(_page_dirty) {
        render();
        _page_dirty = false;
    }

  window.requestAnimationFrame(update)
}

// first line...
new_command_line();
render();
update(0);
