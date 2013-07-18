# http://www.sublimetext.com/docs/commands
# http://www.sublimetext.com/docs/3/api_reference.html

import os
import re
import threading
import subprocess
import sublime
import sublime_plugin


class SnitchSetPanelText(sublime_plugin.TextCommand):
    def run(self, edit, text):
        window = sublime.active_window()
        panel = window.create_output_panel('snitch_panel')
        panel.insert(edit, 0, text)
        window.run_command('show_panel', {'panel': 'output.snitch_panel'})


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


class SnitchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rowcol = self.view.rowcol(self.view.sel()[0].begin())
        self.snitch_line = rowcol[0] + 1
        file_path = self.view.file_name()
        working_dir, filename = os.path.split(file_path)
        hg_cmd = 'hg annotate -l -u -n ' + filename
        git_cmd = 'git blame {f} -L {l},{l}'.format(
            f=filename, l=self.snitch_line)

        CommandRunner(hg_cmd, working_dir, self.hg_callback)
        CommandRunner(git_cmd, working_dir, self.git_callback)

    def hg_callback(self, output):
        if output:
            target_line = output.splitlines()[self.snitch_line - 1]
            patterns = [r'(\s*?\w.*)\s<', r'\s*(\w+)\s\d+']
            for p in patterns:
                matches = re.match(p, target_line)
                if matches:
                    self.apply_blame(matches.group(1).strip())
                    return

    def git_callback(self, output):
        if output:
            matches = re.match(r'\w+\s\((.*?)\s\d+', output)
            if matches:
                self.apply_blame(matches.group(1))

    def apply_blame(self, blame_target):
        print("Snitching on %s" % blame_target)
        s = 'Snitch: Blame line {line} on {name}!'.format(
            line=self.snitch_line,
            name=blame_target)
        self.view.run_command('snitch_set_panel_text', {'text': s})
