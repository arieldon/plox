from abc import ABC, abstractmethod

import expr
import tokens


class Visitor(ABC):
    @abstractmethod
    def visit_expression_stmt(self, stmt):
        raise NotImplementedError

    @abstractmethod
    def visit_print_stmt(self, stmt):
        raise NotImplementedError

    @abstractmethod
    def visit_var_stmt(self, stmt):
        raise NotImplementedError


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor):
        raise NotImplementedError


class Expression(Stmt):
    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor):
        return visitor.visit_expression_stmt(self)


class Print(Stmt):
    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor):
        return visitor.visit_print_stmt(self)


class Var(Stmt):
    def __init__(self, name: tokens.Token, initializer: expr.Expr) -> None:
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: Visitor):
        return visitor.visit_var_stmt(self)
