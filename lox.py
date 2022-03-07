import sys
from typing import ClassVar

import parser
import print_ast
import scanner
import tokens


class Lox:
    had_error: ClassVar[bool] = False

    @staticmethod
    def run_file(filepath: str) -> None:
        try:
            with open(filepath, "r") as f:
                source = f.read()
            Lox.run(source)
        except IOError:
            print(f"unable to read file {filepath}", file=sys.stderr)
            sys.exit(65)

        if Lox.had_error:
            sys.exit(64)

    @staticmethod
    def run_prompt() -> None:
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                return
            Lox.run(line)
            Lox.had_error = False

    @staticmethod
    def run(source: str) -> None:
        s = scanner.Scanner(source)
        t = s.scan_tokens()
        p = parser.Parser(t)
        if (expression := p.parse()):
            print(print_ast.ASTPrinter().format(expression))

        if (Lox.had_error):
            return

    @staticmethod
    def error(item: int | tokens.Token, message: str) -> None:
        if isinstance(item, int):
            line = item
            Lox.report(line, "", message)
        elif isinstance(item, tokens.Token):
            token = item
            if token.token_type == tokens.TokenType.EOF:
                Lox.report(token.line, " at end", message)
            else:
                Lox.report(token.line, f" at '{token.lexeme}'", message)

    @staticmethod
    def report(line: int, where: str, message: str) -> None:
        print(f"[line {line}] error {where}: {message}", file=sys.stderr)
        Lox.had_error = True


def main() -> None:
    lox = Lox()

    argc = len(sys.argv)
    if argc > 2:
        print(f"usage: {sys.argv[0]} [script]")
        sys.exit(1)
    elif argc == 2:
        lox.run_file(sys.argv[1])
    else:
        lox.run_prompt()


if __name__ == "__main__":
    main()
