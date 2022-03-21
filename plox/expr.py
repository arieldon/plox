from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from tokens import Token


R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    @abstractmethod
    def visit_assign_expr(self, expr: Assign) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_binary_expr(self, expr: Binary) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_call_expr(self, expr: Call) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_get_expr(self, expr: Get) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_grouping_expr(self, expr: Grouping) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_literal_expr(self, expr: Literal) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_logical_expr(self, expr: Logical) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_set_expr(self, expr: Set) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_this_expr(self, expr: This) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_super_expr(self, expr: Super) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_unary_expr(self, expr: Unary) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_variable_expr(self, expr: Variable) -> R:
        raise NotImplementedError


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        raise NotImplementedError


class Assign(Expr):
    def __init__(self, name: Token, value: Expr) -> None:
        self.name = name
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_assign_expr(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_binary_expr(self)


class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        self.callee = callee
        self.paren = paren
        self.arguments = arguments

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_call_expr(self)


class Get(Expr):
    def __init__(self, item: Expr, name: Token) -> None:
        self.item = item
        self.name = name

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_get_expr(self)


class Grouping(Expr):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    def __init__(self, value: None | str | float) -> None:
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_literal_expr(self)


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_logical_expr(self)


class Set(Expr):
    def __init__(self, item: Expr, name: Token, value: Expr) -> None:
        self.item = item
        self.name = name
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_set_expr(self)


class Super(Expr):
    def __init__(self, keyword: Token, method: Token) -> None:
        self.keyword = keyword
        self.method = method

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_super_expr(self)


class This(Expr):
    def __init__(self, keyword: Token) -> None:
        self.keyword = keyword

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_this_expr(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr) -> None:
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_unary_expr(self)


class Variable(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_variable_expr(self)
