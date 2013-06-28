# http://www.sublimetext.com/docs/commands
# http://www.sublimetext.com/docs/3/api_reference.html

import os
import re
import threading
import subprocess
import sublime, sublime_plugin


class CommandRunner(threading.Thread):
    def __init__(self, command_str, working_dir, callback=None, name=None):
        threading.Thread.__init__(self)
        self.callback = callback
        self.command = command_str
        self.working_dir = working_dir
        self.start()
        if name is None:
            name = command_str
        self.name = name

    def run(self):
        result = None
        try:
            os.chdir(self.working_dir)
            output = subprocess.check_output(self.command.split(' '))
            result = output.decode("utf-8").strip()
        except Exception as e:
            print(str(e))
            result = None
        if self.callback:
            self.callback(result)


class SnitchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        line = self.get_line_number()
        filename = self.active_view().file_name()
        working_dir = os.path.split(filename)[0]
        hg_cmd = 'hg annotate -l -u -n ' + filename
        git_cmd = 'git blame {f} -L {l},{l}'.format(
            f=filename, l=line)

        print('hg_cmd: {}'.format(hg_cmd))
        print('git_cmd: {}'.format(git_cmd))

        CommandRunner(hg_cmd, working_dir, self.hg_callback)
        CommandRunner(git_cmd, working_dir, self.git_callback)

    def get_line_number(self):
        view = self.active_view()
        point = view.sel()[0].b
        rowcol = view.rowcol(point)
        return rowcol[0] + 1

    def hg_callback(self, output):
        if output:
            print('hg_callback result: ' + output)

    def git_callback(self, output):
        if output:
            print('git_callback result: ' + output)

    def current_scope(self):
        print(self.active_view().scope_name(0))
        return self.active_view().scope_name(0)

    def active_view(self):
        return sublime.active_window().active_view()
