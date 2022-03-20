from __future__ import annotations

import interpreter
import tokens


class Environment:
    def __init__(self, enclosing: None | Environment = None) -> None:
        self.enclosing = enclosing
        self.values: dict[str, object] = {}

    def define(self, name: str, value: object) -> None:
        self.values[name] = value

    def ancestor(self, distance: int) -> Environment:
        env = self
        for i in range(distance):
            env = env.enclosing
        return env

    def get_at(self, distance: int, name: str) -> object:
        return self.ancestor(distance).values[name]

    def assign_at(self, distance: int, name: tokens.Token, value: object) -> None:
        self.ancestor(distance).values[name.lexeme] = value

    def get(self, name: tokens.Token) -> object:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing:
            return self.enclosing.get(name)

        raise interpreter.LoxRuntimeError(name, f"undefined variable '{name.lexeme}'")

    def assign(self, name: tokens.Token, value: object) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
        elif self.enclosing:
            self.enclosing.assign(name, value)
        else:
            raise interpreter.LoxRuntimeError(name, f"undefined variable '{name.lexeme}'")
