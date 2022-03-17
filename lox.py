from __future__ import annotations
import sys

import interpreter
import parser
import scanner
import tokens


intrp = None
had_error = False
had_runtime_error = False


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
    s = scanner.Scanner(source)
    t = s.scan_tokens()
    p = parser.Parser(t)
    statements = p.parse()

    if intrp:
        intrp.interpret(statements)

    if (had_error):
        return


def error(item: int | tokens.Token, message: str) -> None:
    if isinstance(item, int):
        line = item
        report(line, "", message)
    elif isinstance(item, tokens.Token):
        token = item
        if token.token_type == tokens.TokenType.EOF:
            report(token.line, "at end", message)
        else:
            report(token.line, f"at '{token.lexeme}'", message)


def runtime_error(error: interpreter.RunningTimeError) -> None:
    print(error)
    had_runtime_error = True


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] error {where}: {message}", file=sys.stderr)
    had_error = True


def main() -> None:
    global intrp
    intrp = interpreter.Interpreter()

    argc = len(sys.argv)
    if argc > 2:
        print(f"usage: {sys.argv[0]} [script]")
        sys.exit(1)
    elif argc == 2:
        run_file(sys.argv[1])
    else:
        run_prompt()


if __name__ == "__main__":
    main()
