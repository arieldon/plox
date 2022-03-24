from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import expr
import tokens


R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    @abstractmethod
    def visit_block_stmt(self, stmt: Block) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_class_stmt(self, stmt: Class) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_expression_stmt(self, stmt: Expression) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_function_stmt(self, stmt: Function) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_if_stmt(self, stmt: If) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_print_stmt(self, stmt: Print) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_return_stmt(self, stmt: Return) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_while_stmt(self, stmt: While) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_var_stmt(self, stmt: Var) -> R:
        raise NotImplementedError


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        raise NotImplementedError


class Block(Stmt):
    def __init__(self, statements: list[Stmt]) -> None:
        self.statements = statements

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_block_stmt(self)


class Class(Stmt):
    def __init__(
        self, name: tokens.Token, superclass: expr.Variable, methods: list[Function]
    ) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_class_stmt(self)

class Expression(Stmt):
    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_expression_stmt(self)


class Function(Stmt):
    def __init__(
        self, name: tokens.Token, params: list[tokens.Token], body: list[Stmt]
    ) -> None:
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_function_stmt(self)


class If(Stmt):
    def __init__( self, condition: expr.Expr, then_branch: Stmt, else_branch: Stmt) -> None:
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_if_stmt(self)


class Print(Stmt):
    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_print_stmt(self)


class Return(Stmt):
    def __init__(self, keyword: tokens.Token, value: expr.Expr) -> None:
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_return_stmt(self)


class While(Stmt):
    def __init__(self, condition: expr.Expr, body: Stmt) -> None:
        self.condition = condition
        self.body = body

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_while_stmt(self)


class Var(Stmt):
    def __init__(self, variables: dict[tokens.Token, expr.Expr]) -> None:
        self.variables = variables

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_var_stmt(self)
