import time
import os
from Logging import jlog
from flask import json


class ESPNode:
    # seconds before esp times out
    _timeout_period = 5.0
    _local_url = "127.0.0.1"

    def __init__(self, url, default_state):
        if default_state is None:
            self._state = {}
            self.background_script = ""
            self.foreground_script = ""
            self.name = url
            self.clear_subscriptions()
        else:
            self._state = default_state

        self.url = url

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

    @property
    def foreground_script(self):
        return self._state["foreground_script"]

    @foreground_script.setter
    def foreground_script(self, value):
        self._state["foreground_script"] = value

    def subscriptions(self):
        return self._state["subscriptions"]

    def clear_subscriptions(self):
        self._state["subscriptions"] = []

    def add_subscription(self, title):
        self._state["subscriptions"].append(title)

    '''returns true if this esp subscripts to a particular message'''
    def subscribes_to(self, title):
        return title in self._state["subscriptions"]


# factory/manager for connected nodes
class ESPManager:
    _save_folder = "data"
    _save_file = 'esp_save.json'

    def __init__(self):
        self.nodes = {}
        self.hot_node = None
        self._save_path = os.path.join( os.getcwd(), os.path.normpath(self._save_folder),self._save_file)

    # esp node connects to the server.  Return control message to node
    def handle_connection(self, url):
        # first connection?
        if url not in self.nodes:
            esp_save = self._load_esp(url)
            self.nodes[url] = ESPNode(url, esp_save)
            jlog.info("ESP Node Connected: {}".format(url))
        esp = self.nodes[url]
        esp.touch()

        if self.hot_node is None:
            self.hot_node = esp

        return esp.get_control_message()

    def update(self):
        kill_esps = []
        for esp in self.nodes.values():
            if esp.timed_out():
                kill_esps.append(esp)
        for esp in kill_esps:
            del self.nodes[esp.url]
            if self.hot_node == esp:
                self.hot_node = None
            jlog.info("ESP Node Disconnected: {}".format(esp.url))

    def get_node_from_url(self, url):
        if url in self.nodes:
            return self.nodes[url]
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
            return self.hot_node.url
        return None

    def dump_esps(self):
        msg = ""
        esps = self.nodes.values()
        for esp in esps:
            msg = msg + str(esp) + "\n"
        return msg

    # looks for any esps that subscribe to this message.  If they do, then the
    # foreground script for that esp is set based on that message
    # returns the # of esps that subscribe to a given message
    def publish_to_esps(self, title, tcl):
        count = 0
        for esp in self.nodes.values():
            if esp.subscribes_to(title):
                esp.foreground_script = tcl
                count += 1
        return count

    # Stores the current state of the esps
    def store_esps(self):
        with open(self._save_path, 'w') as f:
            esp_save = {esp.url: esp.state for esp in self.nodes.values()}
            f.write(json.dumps(esp_save, indent=4, sort_keys=True))
            return len(esp_save.values())

    # returns the state of an esp from storage
    def _load_esp(self, url):
        if os.path.isfile(self._save_path):
            with open(self._save_path, 'r') as f:
                esp_save = json.load(f)
                if url in esp_save:
                    return esp_save[url]
        return None


# define singleton
esp_manager = ESPManager()
