from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod

import expr
import tokens


class Visitor(ABC):
    @abstractmethod
    def visit_block_stmt(self, stmt: Block) -> Any:
        raise NotImplementedError

    @abstractmethod
    def visit_expression_stmt(self, stmt: Expression) -> Any:
        raise NotImplementedError

    @abstractmethod
    def visit_if_stmt(self, stmt: If) -> Any:
        raise NotImplementedError

    @abstractmethod
    def visit_print_stmt(self, stmt: Print) -> Any:
        raise NotImplementedError

    @abstractmethod
    def visit_var_stmt(self, stmt: Var) -> Any:
        raise NotImplementedError


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor) -> Any:
        raise NotImplementedError


class Block(Stmt):
    def __init__(self, statements: list[None | Stmt]) -> None:
        self.statements = statements

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_block_stmt(self)


class Expression(Stmt):
    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_expression_stmt(self)


class If(Stmt):
    def __init__(
        self, condition: expr.Expr, then_branch: Stmt, else_branch: None | Stmt
    ) -> None:
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_if_stmt(self)


class Print(Stmt):
    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_print_stmt(self)


class Var(Stmt):
    def __init__(self, name: tokens.Token, initializer: None | expr.Expr) -> None:
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_var_stmt(self)
