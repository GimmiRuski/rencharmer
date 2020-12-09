import tempfile

import click

INDENTATION = "    "


@click.command()
@click.option("--file", is_flag=True)
@click.argument("script", type=click.File())
def main(file, script):
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


def get_python_blocks(script):
    block = None
    block_indentation_level = 0
    blocks = []
    for line in script:
        if "python:" in line:
            # Start python block
            block = PythonBlock(line)
        elif block:
            line_has_greater_indentation_level = (
                get_line_indentation_level(line) > block_indentation_level
            )
            if line == "\n" or line_has_greater_indentation_level:
                # Add line to python block
                block.add_line(line)
            else:
                # Finish python block
                blocks.append(block)
                block = None
    if block:
        blocks.append(block)
        block = None
    return blocks


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
