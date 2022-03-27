from __future__ import annotations
import readline
import sys

from interpreter import Interpreter, LoxRuntimeError
from parser import Parser
from resolver import Resolver
from scanner import Scanner
from tokens import Token, TokenType


def run_file(filepath: str) -> None:
    """Input source from a file to Lox interpreter."""
    try:
        with open(filepath, "r") as f:
            source = f.read()
        run(source)
    except IOError:
        print(f"unable to read file '{filepath}'", file=sys.stderr)
        sys.exit(65)

    if had_error:
        sys.exit(64)
    elif had_runtime_error:
        sys.exit(70)


def run_prompt() -> None:
    """Start a REPL and input lines of source to Lox interpreter."""
    global had_error

    while True:
        try:
            multiline = ""
            while True:
                line = input("... " if multiline else ">>> ")
                if (line := line.rstrip()).endswith("\\"):
                    multiline += line.removesuffix("\\")
                elif multiline:
                    multiline += line
                    break
                else:
                    break
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print()
            return

        if multiline:
            line = multiline
        run(line, repl=True)
        had_error = False


def run(source: str, repl: bool = False) -> None:
    """Interpret Lox source code.

    1. Tokenize input.
    2. Parse tokens into syntax trees.
    3. Resolve declarations and definitions of local variables in
       separate pass.
    4. Traverse syntax trees, translate Lox to Python, and execute.
    """
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()
    if had_error:
        return

    resolver = Resolver(interpreter)
    resolver.resolve(statements)
    if had_error:
        return

    interpreter.interpret(statements, repl)


def error(item: int | Token, message: str) -> None:
    """Report error and its location appropriately."""
    if isinstance(item, int):
        line = item
        report(line, "", message)
    elif isinstance(item, Token):
        token = item
        if token.token_type == TokenType.EOF:
            report(token.line, "at end", message)
        else:
            report(token.line, f"at '{token.lexeme}'", message)


def runtime_error(error: LoxRuntimeError) -> None:
    """Output error message and set global runtime error variable."""
    global had_runtime_error

    print(error)
    had_runtime_error = True


def report(line: int, where: str, message: str) -> None:
    """Output error message and set global error variable."""
    global had_error

    print(f"[line {line}] error {where}: {message}", file=sys.stderr)
    had_error = True


interpreter = Interpreter()
had_error = False
had_runtime_error = False
