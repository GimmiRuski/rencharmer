<p align="center">
  <img width="128" height="128" src="https://github.com/GimmiRuski/rencharmer/blob/main/icon.svg">
</p>

<h1 align="center">renCharmer</h1>

A utility script to work with python blocks in Ren'Py scripts.

The name is inspired by [kobaltcore](https://github.com/kobaltcore)'s Ren'Py tools.

## Disclaimer

**renCharmer** is still pretty early on in development, so expect things to break or not work. Given that and its nature (i.e. modifying source code), I would strongly recommend against using it with projects that aren't tracked using a [version control system](https://git-scm.com/).

## Functions

As of right now, **renCharmer** is only capable of two thing:

- Printing python blocks found inside a script
- Formatting python blocks using [black](https://github.com/psf/black)

## Usage

```
$ python3 rencharmer.py -h
Usage: rencharmer.py [OPTIONS] SCRIPT

Options:
  -b, --black                Use black to format python blocks.
  -p, --print-python-blocks  Print the python blocks that are found.
  -h, --help                 Show this message and exit.
```