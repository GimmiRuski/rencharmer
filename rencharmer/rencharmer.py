import tempfile

import click
import sh
from rich.console import Console
from rich.syntax import Syntax

CONSOLE = Console()
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
INDENTATION = "    "


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("-f", "--format", is_flag=True, help="Use black to format python blocks.")
@click.option(
    "-p",
    "--print-python-blocks",
    is_flag=True,
    help="Print the python blocks that are found.",
)
@click.argument("script", type=click.File())
def main(script, format, print_python_blocks):
    script = RenpyScript(script)
    python_block_count = len(script.python_blocks)
    plurality = "" if python_block_count == 1 else "s"
    CONSOLE.log(f"Found {python_block_count} python block{plurality} in {script.path}")
    for python_block_index in range(python_block_count):
        python_block = script.python_blocks[python_block_index]
        if format:
            file_path = create_temporary_file(python_block)
            CONSOLE.log(
                f"Copied python block {python_block_index} contents into {file_path}"
            )
            sh.black("--target-version=py27", file_path)
            CONSOLE.log(f"Formatted {file_path} with black")
            modified_lines = read_temporary_file(file_path)
            script.replace_python_block(python_block, modified_lines)
            CONSOLE.log(
                f"Replaced python block {python_block_index} in {script.path} with {file_path} contents"
            )
            script.save_changes()
            CONSOLE.log(f"Saved {script.path} changes")
        elif print_python_blocks:
            CONSOLE.log(
                f"Printing python block {python_block_index} from {script.path}"
            )
            code = str(python_block)
            syntax = Syntax(code, "python", line_numbers=True)
            CONSOLE.print(syntax)


def create_temporary_file(python_block):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as output_file:
        indentation_level = python_block.indentation_level + 1
        output_file.writelines(
            line.content.replace(INDENTATION, "", indentation_level)
            for line in python_block.lines
        )
        return output_file.name


def read_temporary_file(file_path):
    lines = []
    with open(file_path, "r") as file:
        for line_index, line in enumerate(file):
            line = RenpyScriptLine(line, line_index)
            lines.append(line)
    return lines


class RenpyScript:
    def __init__(self, file):
        self._file = file
        self._lines = None

    @property
    def file(self):
        return self._file

    @property
    def lines(self):
        if self._lines is None:
            self._lines = []
            for index, line in enumerate(self.file):
                script_line = RenpyScriptLine(line, index)
                self._lines.append(script_line)
        return self._lines

    @lines.setter
    def lines(self, lines):
        for line_index, line in enumerate(lines):
            line.index = line_index
        self._lines = lines

    @property
    def path(self):
        return self.file.name

    @property
    def python_blocks(self):
        block = None
        python_blocks = []
        for line in self.lines:
            if "python:" in line.content:
                block = PythonBlock(line.indentation_level)
            elif block:
                if line.is_empty or line.indentation_level > block.indentation_level:
                    block.lines.append(line)
                else:
                    python_blocks.append(block)
                    block = None
        if block:
            python_blocks.append(block)
            block = None
        return python_blocks

    def replace_python_block(self, python_block, modified_lines):
        for line in modified_lines:
            if not line.is_empty:
                # We need to indent the line to match the original python
                # block's indentation.
                indentation = INDENTATION * (python_block.indentation_level + 1)
                line.content = indentation + line.content
        # Select the script's lines without including the old python block.
        lines_first_half = self.lines[0 : python_block.first_line.index]
        lines_second_half = self.lines[python_block.last_line.index + 1 :]
        # Merge the lines together.
        self.lines = lines_first_half + modified_lines + lines_second_half

    def save_changes(self):
        with open(self.path, "w") as file:
            file.writelines(line.content for line in self.lines)


class RenpyScriptLine:
    def __init__(self, content, index):
        self.content = content
        self.index = index

    @property
    def indentation_level(self):
        return self.content.count(INDENTATION)

    @property
    def is_empty(self):
        return self.content == "\n"


class PythonBlock:
    def __init__(self, indentation_level):
        self._indentation_level = indentation_level
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


if __name__ == "__main__":
    main()
