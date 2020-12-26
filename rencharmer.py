import tempfile

import click

INDENTATION = "    "


@click.command()
@click.option("--file", is_flag=True)
@click.argument("script", type=click.File())
def main(file, script):
    script = RenpyScript(script)
    for python_block in script.python_blocks:
        if file:
            file_path = create_output_file(python_block)
            click.echo(file_path)
        else:
            click.echo(python_block)


def create_output_file(python_block):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as output_file:
        output_file.writelines(python_block.lines)
        return output_file.name


class RenpyScript(object):
    def __init__(self, script):
        self._lines = None
        self._python_blocks = None
        self._script = script

    @property
    def lines(self):
        if self._lines is None:
            self._lines = []
            for index, line in enumerate(self.script):
                script_line = RenpyScriptLine(line, index)
                self._lines.append(script_line)
        return self._lines

    @property
    def path(self):
        return self.script.name

    @property
    def python_blocks(self):
        if self._python_blocks is None:
            block = None
            self._python_blocks = []
            for line in self.lines:
                if "python:" in line.content:
                    block = PythonBlock(line)
                elif block:
                    if (
                        line.is_empty
                        or line.indentation_level > block.indentation_level
                    ):
                        block.add_line(line)
                    else:
                        self._python_blocks.append(block)
                        block = None
            if block:
                self._python_blocks.append(block)
                block = None
        return self._python_blocks

    @property
    def script(self):
        return self._script


class RenpyScriptLine(object):
    def __init__(self, content, index):
        self._content = content
        self._index = index

    @property
    def content(self):
        return self._content

    @property
    def indentation_level(self):
        return self.content.count(INDENTATION)

    @property
    def index(self):
        return self._index

    @property
    def is_empty(self):
        return self.content == "\n"


class PythonBlock(object):
    def __init__(self, initialization_line):
        self._indentation_level = initialization_line.indentation_level
        self.lines = []

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def __str__(self):
        return "".join(line.content for line in self.lines)

    @property
    def first_line(self):
        return self.lines[0]

    @property
    def indentation_level(self):
        return self._indentation_level

    @property
    def last_line(self):
        return self.lines[-1]

    @property
    def size(self):
        return len(self.lines)

    def add_line(self, line):
        self.lines.append(line)


if __name__ == "__main__":
    main()
