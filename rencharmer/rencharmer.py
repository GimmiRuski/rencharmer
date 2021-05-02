import re
import tempfile

import click
import sh
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

BLACK_LINE_LENGTH = 88
CONSOLE = Console()
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
DISABLED_PYLINT_MESSAGES = ",".join(
    ["missing-module-docstring", "undefined-variable", "useless-object-inheritance"]
)
INDENTATION = "    "
INDENTATION_LENGTH = len(INDENTATION)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-a", "--analyze", is_flag=True, help="Use pylint to analyze python blocks."
)
@click.option("-d", "--debug", is_flag=True, help="Show debugging messages.")
@click.option("-f", "--format", is_flag=True, help="Use black to format python blocks.")
@click.option(
    "-p",
    "--print",
    is_flag=True,
    help="Print the python blocks that are found.",
)
@click.version_option(None, "-v", "--version")
@click.argument("scripts", nargs=-1, type=click.File())
def main(scripts, analyze, debug, format, print):
    # pylint: disable=redefined-builtin
    task = "Analyzing" if analyze else "Formatting" if format else "Printing"
    with CONSOLE.status(f"{task}..."):
        for script in scripts:
            script = RenpyScript(script)
            if debug:
                CONSOLE.log(f"Working on {script.path}")
            python_block_count = len(script.python_blocks)
            if debug:
                plurality = "" if python_block_count == 1 else "s"
                CONSOLE.log(
                    f"Found {python_block_count} python block{plurality} in {script.path}"
                )
            for python_block_index in range(python_block_count):
                python_block = script.python_blocks[python_block_index]
                if analyze:
                    analyze_python_block(
                        script, python_block, python_block_index, debug
                    )
                elif format:
                    format_python_block(script, python_block, python_block_index, debug)
                elif print:
                    print_python_block(script, python_block, python_block_index)


def analyze_python_block(script, python_block, python_block_index, debug):
    file = PythonBlockFile(python_block)
    if debug:
        CONSOLE.log(
            f"Copied python block {python_block_index} contents into {file.path}"
        )
    output = sh.pylint(  # pylint: disable=no-member
        f"--disable={DISABLED_PYLINT_MESSAGES}",
        "--exit-zero",
        "--jobs=0",
        "--score=no",
        file.path,
    )
    if debug:
        CONSOLE.log(f"Analyzed {file.path} with pylint")
    output = output.replace(file.path, script.path)
    if debug:
        CONSOLE.log("Replaced temporary file path with script path in pylint output")
    output_lines = output.split("\n")
    output_lines = output_lines[1:-1]
    if debug:
        CONSOLE.log("Removed first and last lines from pylint output")
    output_lines = update_line_references(output_lines, python_block)
    if debug:
        CONSOLE.log("Updated line references in pylint output")
    output = "\n".join(output_lines)
    if output:
        CONSOLE.print(output, emoji=False)


def format_python_block(script, python_block, python_block_index, debug):
    indentation_level = python_block.indentation_level + 1
    indentation = indentation_level * INDENTATION_LENGTH
    line_length = BLACK_LINE_LENGTH - indentation
    file = PythonBlockFile(python_block)
    if debug:
        CONSOLE.log(f"Copied python block {python_block_index} into {file.path}")
    sh.black(  # pylint: disable=no-member
        f"--line-length={line_length}", "--target-version=py27", file.path
    )
    if debug:
        CONSOLE.log(f"Formatted {file.path} with black")
    script.replace_python_block(python_block, file.lines)
    if debug:
        CONSOLE.log(
            f"Replaced python block {python_block_index} in {script.path} with {file.path} contents"
        )
    script.save_changes()
    if debug:
        CONSOLE.log(f"Saved {script.path} changes")


def print_python_block(script, python_block, python_block_index):
    CONSOLE.print(f"Printing python block {python_block_index} from {script.path}")
    code = str(python_block)
    syntax = Syntax(code, "python", line_numbers=True)
    panel = Panel(syntax)
    CONSOLE.print(panel)


def update_line_references(lines, python_block):
    updated_lines = []
    for line in lines:
        match = re.search(":(?P<line>[0-9]+):(?P<column>[0-9]+):", line)
        line_number, column_number = match.groups()
        line_number = python_block.first_line.index + int(line_number)
        indentation = (python_block.indentation_level + 1) * INDENTATION_LENGTH
        column_number = indentation + int(column_number) + 1
        old_position = match[0]
        new_position = f":{line_number}:{column_number}:"
        line = line.replace(old_position, new_position)
        updated_lines.append(line)
    return updated_lines


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


class PythonBlockFile:
    def __init__(self, python_block):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as file:
            indentation_level = python_block.indentation_level + 1
            file.writelines(
                line.content.replace(INDENTATION, "", indentation_level)
                for line in python_block.lines
            )
            self._path = file.name

    @property
    def path(self):
        return self._path

    @property
    def lines(self):
        lines = []
        with open(self.path, "r") as file:
            for line_index, line in enumerate(file):
                line = RenpyScriptLine(line, line_index)
                lines.append(line)
        return lines


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
