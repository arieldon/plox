from __future__ import annotations
import sys

from interpreter import Interpreter
from parser import Parser
from resolver import Resolver
from scanner import Scanner
from tokens import Token, TokenType


def run_file(filepath: str) -> None:
    try:
        with open(filepath, "r") as f:
            source = f.read()
        run(source)
    except IOError:
        print(f"unable to read file {filepath}", file=sys.stderr)
        sys.exit(65)

    if had_error:
        sys.exit(64)
    elif had_runtime_error:
        sys.exit(70)


def run_prompt() -> None:
    while True:
        try:
            line = input("> ")
        except EOFError:
            print()
            return
        run(line)
        had_error = False


def run(source: str) -> None:
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

    interpreter.interpret(statements)


def error(item: int | Token, message: str) -> None:
    if isinstance(item, int):
        line = item
        report(line, "", message)
    elif isinstance(item, Token):
        token = item
        if token.token_type == TokenType.EOF:
            report(token.line, "at end", message)
        else:
            report(token.line, f"at '{token.lexeme}'", message)


def runtime_error(error: interpreter.RunningTimeError) -> None:
    print(error)
    had_runtime_error = True


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] error {where}: {message}", file=sys.stderr)
    had_error = True


interpreter = Interpreter()
had_error = False
had_runtime_error = False