import cmd
import os
from TCLHandler import TCLHandler

_data_folder = r".\tcl"

class CommandParser(cmd.Cmd):

    def __init__(self):
        self.tcl = TCLHandler()

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
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics(self.doc_header, cmds_doc, 15, 80)
            self.print_topics(self.misc_header, list(help.keys()), 15, 80)
            self.print_topics(self.undoc_header, cmds_undoc, 15, 80)

    # ----------------------------------------------------------------------------------
    # I/O -- Returns
    # ----------------------------------------------------------------------------------

    def _msg_form(self, text):
        return {"type": "message",
                "message" : text}

    def _tcl_form(self, path, version, tcl_text):
        fname = os.path.basename(path)
        return {"type": "tcl",
                "message" : "Source {}".format(path),
                "filename" : self.tcl.get_basename(fname),
                "version" : version,
                "code" : tcl_text }


    # ----------------------------------------------------------------------------------
    # COMMANDS
    # ----------------------------------------------------------------------------------

    def do_greet(self, arg):
        'A good greeting'
        return self._msg_form("Nice to see you")

    def do_dir(self, arg):
        'List all tcl files: dir'
        return self._msg_form(self.tcl.file_list())

    def do_load(self, arg):
        'Load a file:  load <filename>'
        file_name, version, tcl_buffer = self.tcl.load(arg)
        return self._tcl_form(file_name, version, tcl_buffer)

    def do_save(self, arg):
        'Save previously loaded file:  save'
        file_name, version, tcl_buffer = self.tcl.save(self._tcl_buffer)
        return self._tcl_form(file_name, version, tcl_buffer)

    def default(self, arg):
        return self._msg_form("Unknown Command: `{}`".format(arg))

    def parse(self, command, tcl):
        self._tcl_buffer = tcl
        l = self.precmd(command)
        r = self.onecmd(l)
        r = self.postcmd(r, l)
        return r
