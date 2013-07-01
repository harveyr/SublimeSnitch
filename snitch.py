# http://www.sublimetext.com/docs/commands
# http://www.sublimetext.com/docs/3/api_reference.html

import os
import re
import threading
import subprocess
import sublime
import sublime_plugin


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
            output = subprocess.check_output(self.command, shell=True)
            result = output.decode("utf-8").strip()
        except Exception:
            result = None

        if self.callback:
            self.callback(result)


class SnitchclearCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase_status('sublime_snitch')


class SnitchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print('Snitching...')
        self.snitch_line = self.get_line_number()
        file_path = self.active_view().file_name()
        working_dir, filename = os.path.split(file_path)
        hg_cmd = 'hg annotate -l -u -n ' + filename
        git_cmd = 'git blame {f} -L {l},{l}'.format(
            f=filename, l=self.snitch_line)

        CommandRunner(hg_cmd, working_dir, self.hg_callback)
        CommandRunner(git_cmd, working_dir, self.git_callback)

    def get_line_number(self):
        view = self.active_view()
        self.snitch_point = view.sel()[0].a
        point = self.snitch_point
        rowcol = view.rowcol(point)
        return rowcol[0] + 1

    def hg_callback(self, output):
        if output:
            target_line = output.splitlines()[self.snitch_line - 1]
            matches = re.match(r'\s*(\w+)\s\d+', target_line)
            if matches:
                self.apply_blame(matches.group(1).strip())
            else:
                print('SublimeSnitch: no mercurial matches')

    def git_callback(self, output):
        if output:
            matches = re.match(r'\w+\s\((.*?)\s\d+', output)
            if matches:
                self.apply_blame(matches.group(1))
            else:
                print('SublimeSnitch: no git matches')

    def apply_blame(self, blame_target):
        print("Snitching on %s" % blame_target)
        s = 'Snitch: Blame line {line} on {name}!'.format(
            line=self.snitch_line,
            name=blame_target)
        self.view.set_status('sublime_snitch', s)

    def active_view(self):
        return sublime.active_window().active_view()
