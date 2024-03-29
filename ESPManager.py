import time
import os
from Logging import jlog
from flask import json
from mqq_handler import mqq_handler

class ESPNode:
    # seconds before esp times out
    _timeout_period = 15.0
    _local_url = "127.0.0.1"
    _local_mac = "00:00:00:00:00:00"

    def __init__(self, mac, url, default_state):
        if default_state is None:
            self._state = {}
            self.background_script = ""
            self.foreground_script = ""
            self.name = mac
        else:
            self._state = default_state

        self.url = url
        self.mac = mac

        # last message sent to node.  First time send everything
        self._sent_state = {}
        # timer...
        self._last_connection = None

    def __str__(self):
        msg = ", ".join(["{}:{}".format(k, v) for k, v in self._state.items()])
        msg = '"{}" --> {}'.format(self.name, msg)
        return msg

    # return message that is sent to each esp from "control" endpoint
    def get_control_message(self, force=False):
        c_msg = {k: v for k, v in self._state.items() if not k in self._sent_state or v != self._sent_state[k]}
        self._sent_state = self._state.copy()
        # foreground script is transmitted just 1 time.
        self.foreground_script = ""
        return c_msg

    def touch(self):
        self._last_connection = time.time()

    def timed_out(self):
        # don't time out on local.
        if self.url == self._local_url:
            return False
        return self.age > self._timeout_period

    @property
    def state(self):
        return self._state

    # returns the amount of time since last "touched"
    @property
    def age(self):
        return time.time() - self._last_connection

    @property
    def mac(self):
        return self._state["mac"]

    @mac.setter
    def mac(self, value):
        self._state["mac"] = value

    @property
    def url(self):
        return self._state["url"]

    @url.setter
    def url(self, value):
        self._state["url"] = value

    @property
    def name(self):
        return self._state["name"]

    @name.setter
    def name(self, value):
        self._state["name"] = value

    @property
    def background_script(self):
        return self._state["background_script"]

    @background_script.setter
    def background_script(self, value):
        self._state["background_script"] = value
        # updates background script on esp via mqq
        if value is not None and len(value) > 0:
            mqq_handler.publish("esp/{}/background_script".format(self.name), value)


    @property
    def foreground_script(self):
        return self._state["foreground_script"]

    @foreground_script.setter
    def foreground_script(self, value):
        self._state["foreground_script"] = value
        # updates foreground script on esp via mqq
        if value is not None and len(value) > 0:
            mqq_handler.publish("esp/{}/foreground_script".format(self.name), value)


# factory/manager for connected nodes
class ESPManager:
    _save_folder = "data"
    _save_file = 'esp_save.json'

    def __init__(self):
        self.nodes = {}
        self.hot_node = None
        self._save_path = os.path.join( os.getcwd(), os.path.normpath(self._save_folder),self._save_file)

    def init(self):
        self.refresh_node_list()

    def get_node_from_mac(self, mac):
        if mac in self.nodes:
            return self.nodes[mac]
        return None

    def get_node_from_name(self, name):
        name = next([v for v in self.nodes.values() if v.name == name])
        return name

    @property
    def hot_node(self):
        return self._hot_node

    @hot_node.setter
    def hot_node(self, esp):
        self._hot_node = esp

    # pushes a script to the foreground of the "hot" esp node.  Node should grab
    # this script on next connection
    def run_hot_script(self, tcl_buffer):
        if self.hot_node is not None:
            self.hot_node.foreground_script = tcl_buffer
            return self.hot_node.mac
        return None

    def dump_esps(self):
        msg = ""
        esps = self.nodes.values()
        for esp in esps:
            msg = msg + str(esp) + "\n"
        return msg

    # Stores the current state of the esps
    def store_esps(self):
        with open(self._save_path, 'w') as f:
            esp_save = {esp.mac: esp.state for esp in self.nodes.values()}
            f.write(json.dumps(esp_save, indent=4, sort_keys=True))
            return len(esp_save.values())

    # returns the state of an esp from storage
    def _load_esp(self, mac):
        if os.path.isfile(self._save_path):
            with open(self._save_path, 'r') as f:
                esp_save = json.load(f)
                if mac in esp_save:
                    return esp_save[mac]
        return None


    def refresh_node_list(self):
        self.nodes = {}
        self.hot_node = None

        # this function will
        mqq_handler.add_callback("esp/log", self._handle_node_messages)

        # connected esps will respond to this message
        mqq_handler.publish("esp/ping_all", "")

    # push mqq log message into log q.
    def _handle_node_messages(self, client, obj, msg):

        print("NODE MESSAGE: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        log_data = json.loads(msg.payload)

        client_name = log_data["client"]
        if client_name not in self.nodes:
            esp_save = self._load_esp(client_name)
            self.nodes[client_name] = ESPNode(client_name, client_name, esp_save)
            jlog.info("ESP Node Connected: {}".format(client_name))
            self.nodes[client_name].touch()
            if self.hot_node is None:
                self.hot_node = self.nodes[client_name]

# define singleton
esp_manager = ESPManager()
