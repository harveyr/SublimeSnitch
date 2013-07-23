import os
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
        selection = self.view.sel()
        rowcol = self.view.rowcol(selection[0].begin())
        self.snitch_line = rowcol[0] + 1

        self.line_count = len(self.view.lines(selection[0]))

        file_path = self.view.file_name()
        working_dir, filename = os.path.split(file_path)
        hg_cmd = 'hg annotate -l -u -n -c -d -q ' + filename
        git_cmd = 'git blame {f} -L {l1},{l2}'.format(
            f=filename,
            l1=self.snitch_line,
            l2=self.snitch_line + self.line_count - 1)

        CommandRunner(hg_cmd, working_dir, self.hg_callback)
        CommandRunner(git_cmd, working_dir, self.git_callback)

    def hg_callback(self, output):
        if output:
            l1 = self.snitch_line - 1
            l2 = l1 + self.line_count
            lines = output.splitlines()[l1:l2]
            self.apply_blame('\n'.join(lines))

    def git_callback(self, output):
        if output:
            self.apply_blame(output)

    def apply_blame(self, results):
        s = '[Snitch] Blame Results:\n{result}'.format(
            result=results)
        self.view.run_command('snitch_set_panel_text', {'text': s})
