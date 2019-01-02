import cmd
import os

from ESPManager import esp_manager
from PubSub import PubSubBroker
from TCLHandler import TCLHandler

_data_folder = r".\tcl"


class CommandParser(cmd.Cmd):

    def __init__(self):
        super().__init__()
        self.tcl = TCLHandler()
        self._tcl_buffer = None

    # overriding help function so help text is returned...
    def do_help(self, arg):
        'List available commands with "help" or detailed help with "help cmd".'
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        return self._msg_form(doc)
                        # self.stdout.write("%s\n" % str(doc))
                        # return
                except AttributeError:
                    pass
                return self._msg_form(self.nohelp % (arg,))
                # self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
                # return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]] = 1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd = name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            # self.stdout.write("%s\n" % str(self.doc_leader))
            # self.print_topics(self.doc_header, cmds_doc, 15, 80)
            # self.print_topics(self.misc_header, list(help.keys()), 15, 80)
            # self.print_topics(self.undoc_header, cmds_undoc, 15, 80)
            return self._msg_form(",".join(cmds_undoc))

    # ----------------------------------------------------------------------------------
    # I/O -- Returns
    # ----------------------------------------------------------------------------------

    def _msg_form(self, text):
        return {"type": "message",
                "message": text}

    def _tcl_form(self, path, version, tcl_text):
        fname = os.path.basename(path)
        return {"type": "data",
                "message": "Source {}".format(path),
                "filename": self.tcl.get_basename(fname),
                "version": version,
                "code": tcl_text}

    # ----------------------------------------------------------------------------------
    # COMMANDS
    # ----------------------------------------------------------------------------------

    def do_greet(self, arg):
        'A good greeting'
        return self._msg_form("Nice to see you.  All systems running")

    # TCL ----------------------------------------------
    def do_dir(self, arg):
        'List all data files: dir'
        return self._msg_form(self.tcl.file_list())

    def do_load(self, arg):
        'Load a file:  load <filename>'
        file_name, version, tcl_buffer = self.tcl.load(arg)
        return self._tcl_form(file_name, version, tcl_buffer)

    def do_save(self, arg):
        'Save to previously loaded file:  save'
        file_name, version, tcl_buffer = self.tcl.save(self._tcl_buffer)
        return self._tcl_form(file_name, version, tcl_buffer)

    def do_run(self, arg):
        'Sends/executes script to connected esp:  run'
        if len(self._tcl_buffer) == 0:
            return self._msg_form("Error...  empty data buffer... no script to run")

        if esp_manager.hot_node is None:
            return self._msg_form("Error...  no esp is 'hot'")

        esp_manager.hot_node.foreground_script = self._tcl_buffer

        return self._msg_form("Script Started On: `{}`".format(esp_manager.hot_node))

    # ESP ---------------------------------------------
    def do_esps(self, arg):
        """Lists the active ESP Devices:  esps"""
        return self._msg_form(esp_manager.dump_esps())

    def do_store(self, arg):
        """Stores the current state of the esps:  store"""
        count = esp_manager.store_esps()
        return  self._msg_form("{} Esps Stored".format(count))

    def do_hot(self, arg):
        'Sets the hot node OR returns the current hot node [<url>]'
        if len(arg) > 0:
            esp = esp_manager.get_node_from_url(arg)
            esp_manager.hot_node = esp
        else:
            esp = esp_manager.hot_node
        return self._msg_form("HOT:  {}".format(esp))

    def do_name(self, arg):
        """Names the hot esp:  <name>"""
        esp = esp_manager.hot_node
        esp.name = arg
        return self._msg_form("Renamed:   {}".format(esp))

    def do_subscribeto(self, arg):
        'Adds subscription to hot node <topic title>'
        esp = esp_manager.hot_node
        esp.add_subscription(arg)
        return self._msg_form("Subscribes:   {}".format(esp))

    def do_publish(self, arg):
        'Publishes a message to esps:  publish <topic title>'
        count = PubSubBroker.publish(arg)
        return  self._msg_form("{} Subscribed to '{}'".format(count, arg))

    def default(self, arg):
        return self._msg_form("Unknown Command: `{}`".format(arg))

    def parse(self, command, tcl):
        self._tcl_buffer = tcl
        l = self.precmd(command)
        r = self.onecmd(l)
        r = self.postcmd(r, l)
        return r
