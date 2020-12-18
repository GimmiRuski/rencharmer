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
        self.script = script
        self._python_blocks = None
        self._python_initialization_lines = None

    @property
    def path(self):
        return self.script.name

    @property
    def python_blocks(self):
        if self._python_blocks is None:
            block = None
            self._python_blocks = []
            for line in self.script:
                line = RenpyScriptLine(line)
                if "python:" in line:
                    # Start python block
                    block = PythonBlock(line)
                elif block:
                    if line == "\n" or line.indentation_level > block.indentation_level:
                        # Add line to python block
                        block.add_line(line)
                    else:
                        # Finish python block
                        self._python_blocks.append(block)
                        block = None
            if block:
                self._python_blocks.append(block)
                block = None
        return self._python_blocks

    @property
    def python_initialization_lines(self, script):
        if self._python_initialization_lines is None:
            self._python_initialization_lines = []
            for i, line in enumerate(script):
                if "python:" in line:
                    self._python_initialization_lines.append(i)
        return self._python_initialization_lines


class RenpyScriptLine(str):
    @property
    def indentation_level(self):
        return self.count(INDENTATION)


class PythonBlock(object):
    def __init__(self, initialization_line):
        self._indentation_level = initialization_line.indentation_level
        self.lines = []

    def __str__(self):
        return "".join(self.lines)

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    @property
    def indentation_level(self):
        return self._indentation_level

    @property
    def size(self):
        return len(self.lines)

    def add_line(self, line):
        line = line.replace(INDENTATION, "", self.indentation_level + 1)
        self.lines.append(line)


if __name__ == "__main__":
    main()
