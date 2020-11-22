import click

INDENTATION = "    "


@click.command()
@click.argument("script", type=click.File())
def main(script):
    blocks = get_python_blocks(script)
    for block in blocks:
        click.echo(block)


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


def get_line_indentation_level(line):
    return line.count(INDENTATION)


class PythonBlock(object):
    def __init__(self, initialization_line):
        self._indentation_level = get_line_indentation_level(initialization_line)
        self.lines = []

    def add_line(self, line):
        line = line.replace(INDENTATION, "", self.indentation_level + 1)
        self.lines.append(line)

    def __str__(self):
        return "".join(self.lines)

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    @property
    def indentation_level(self):
        return self._indentation_level


if __name__ == "__main__":
    main()
