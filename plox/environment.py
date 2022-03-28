from __future__ import annotations

import interpreter
import tokens


class Environment:
    """Table of bindings that associates variables to values.

    Parameters
    ----------
    enclosing : Environment
        Environment that wraps new environment created

    Attributes
    ----------
    enclosing : Environment
        Environment that wraps new environment created
    values : dict[str, object]
        Map of variables to values
    """
    def __init__(self, enclosing: Environment = None) -> None:
        self.enclosing = enclosing
        self.values: dict[str, object] = {}

    def define(self, name: str, value: object) -> None:
        """Define a (new) value in the environment."""
        self.values[name] = value

    def ancestor(self, distance: int) -> Environment:
        """Return enclosing environment some distance from current."""
        env = self
        for i in range(distance):
            env = env.enclosing
        return env

    def get_at(self, distance: int, name: str) -> object:
        """Return value from some enclosing environment.

        Parameters
        ----------
        distance : int
            Distance from current environment to desired ancestor or
            enclosing environment
        name : str
            Key of value to return
        """
        return self.ancestor(distance).values[name]

    def assign_at(self, distance: int, name: tokens.Token, value: object) -> None:
        """Set value for some enclosing environment.

        Parameters
        ----------
        distance : int
            Distance from current environment to desired ancestor or
            enclosing environment
        name : tokens.Token
            Token with lexeme to use as key
        value : object
            Value to associate with key
        """
        self.ancestor(distance).values[name.lexeme] = value

    def get(self, name: tokens.Token) -> object:
        """Retrieve a value from the environment.

        Parameters
        ----------
        name : tokens.Token
            Token with lexeme to use as key

        Raises
        ------
        LoxRuntimeError
            Raise a runtime exception when undefined variable are used
        """
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing:
            return self.enclosing.get(name)

        raise interpreter.LoxRuntimeError(name, f"undefined variable '{name.lexeme}'")

    def assign(self, name: tokens.Token, value: object) -> None:
        """Update a value in the environment.

        Parameters
        ----------
        name : tokens.Token
            Token with lexeme to use as key
        value : object
            New value

        Raises
        ------
        LoxRuntimeError
            Raise a runtime exception on attempt to update a key-value
            pair that does not exist
        """
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
        elif self.enclosing:
            self.enclosing.assign(name, value)
        else:
            raise interpreter.LoxRuntimeError(name, f"undefined variable '{name.lexeme}'")
