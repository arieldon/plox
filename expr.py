from abc import ABC, abstractmethod

from tokens import Token


class Visitor(ABC):
    @abstractmethod
    def visit_binary_expr(self, expr):
        raise NotImplementedError

    @abstractmethod
    def visit_grouping_expr(self, expr):
        raise NotImplementedError

    @abstractmethod
    def visit_literal_expr(self, expr):
        raise NotImplementedError

    @abstractmethod
    def visit_unary_expr(self, expr):
        raise NotImplementedError


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        raise NotImplementedError


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor):
        return visitor.visit_binary_expr(self)


class Grouping(Expr):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor):
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    def __init__(self, value: None | str | float) -> None:
        self.value = value

    def accept(self, visitor: Visitor):
        return visitor.visit_literal_expr(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr) -> None:
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor):
        return visitor.visit_unary_expr(self)
