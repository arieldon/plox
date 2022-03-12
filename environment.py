from __future__ import annotations

import interpreter
import tokens


class Environment:
    def __init__(self, enclosing: None | Environment = None) -> None:
        self.enclosing = enclosing
        self.values: dict[str, object] = {}

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def get(self, name: tokens.Token) -> object:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing:
            return self.enclosing.get(name)

        raise interpreter.RunningTimeError(name, f"undefined variable '{name.lexeme}'")

    def assign(self, name: tokens.Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
        elif self.enclosing:
            self.enclosing.assign(name, value)
        else:
            raise interpreter.RunningTimeError(name, f"undefined variable '{name.lexeme}'")
