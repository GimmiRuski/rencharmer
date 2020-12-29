<p align="center">
  <img width="128" height="128" src="https://github.com/GimmiRuski/rencharmer/blob/main/icon.svg">
</p>

<h1 align="center">renCharmer</h1>

<p align="center">A utility script to work with python blocks inside Ren'Py scripts.</p>

## Disclaimer

**renCharmer** is still pretty early on in development, so expect things to break or not work. Given that and its nature (i.e. modifying source code), I would strongly recommend against using it with projects that aren't tracked using a [version control system](https://git-scm.com/).

## Functions

As of right now, **renCharmer** is capable of doing the following:

- Analyzing python blocks using [pylint](https://github.com/PyCQA/pylint)
- Formatting python blocks using [black](https://github.com/psf/black)

## Installation

```
pip install rencharmer
```

## Usage

```
$ rencharmer -h
Usage: rencharmer [OPTIONS] [SCRIPTS]...

Options:
  -a, --analyze  Use pylint to analyze python blocks.
  -d, --debug    Show debugging messages.
  -f, --format   Use black to format python blocks.
  -p, --print    Print the python blocks that are found.
  -v, --version  Show the version and exit.
  -h, --help     Show this message and exit.
```

## Credits

- The name is inspired by [kobaltcore](https://github.com/kobaltcore)'s Ren'Py tools
- The icon is from [game-icons.net](https://game-icons.net/)
