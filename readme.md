# Plox
Plox is a tree-walk interpreter for Lox from Part II of Robert Nystrom's
[Crafting Interpreters](http://craftinginterpreters.com/).

Aside from the features implemented and explained in the book, Plox also
supports:

- Nestable block comments;
- Comma expressions;
- Ternary or conditional expressions;
- Output of expressions without explicit `print` statements in the REPL;
- Termination of loops with `break` statements;
- Errors for unused local variables.


## Usage
```
$ python -m plox [script]
```

Run Plox without a script to enter the REPL. There are also scripts located in
directory `examples/`.


## Installation
```
$ python -m pip install git+https://github.com/arieldon/plox.git#egg=plox
```
