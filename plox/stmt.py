from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from plox import expr
from plox import tokens


R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    """Interface other objects inherit and implement for its types."""

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
    def visit_break_stmt(self, stmt: Break) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_while_stmt(self, stmt: While) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_var_stmt(self, stmt: Var) -> R:
        raise NotImplementedError


class Stmt(ABC):
    """Abstract class from which all statements inherit.

    Statements must implement a method accept() because other classes,
    namely `Interpreter` and `Resolver` use the visitor pattern. This
    pattern allows different classes to implement different behavior for
    the same types without changing the types themselves.
    """

    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        raise NotImplementedError


class Block(Stmt):
    """Represent some block that contains many statements.

    Parameters
    ----------
    statements : list[Stmt]
        List of statements within the block
    """

    def __init__(self, statements: list[Stmt]) -> None:
        self.statements = statements

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_block_stmt(self)


class Class(Stmt):
    """Represent a statement that declares and defines a new class.

    Parameters
    ----------
    name : tokens.Token
        Token that contains name of class
    superclass : expr.Variable
        Variable expression that defines parent of this class
    methods : list[Function]
        Functions accessible from instance of a class
    """

    def __init__(
        self, name: tokens.Token, superclass: expr.Variable, methods: list[Function]
    ) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_class_stmt(self)

class Expression(Stmt):
    """Represent statement that contains an expression.

    Parameters
    ----------
    expression : expr.Expr
        Statement within expression
    """

    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_expression_stmt(self)


class Function(Stmt):
    """Represent statement that declares and defines a function.

    Parameters
    ----------
    name : tokens.Token
        Token that contains name of function
    params : list[tokens.Token]
        Parameters required by function
    body : list[Stmt]
        Statements the function executes
    """

    def __init__(
        self, name: tokens.Token, params: list[tokens.Token], body: list[Stmt]
    ) -> None:
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_function_stmt(self)


class If(Stmt):
    """Represent a conditional if-else statement.

    Parameters
    ----------
    condition : Expr
        Expression to that decides the branch
    then_branch : Expr
        Statement or block of statements to execute if true
    else_branch : Expr
        Statement or block of statements to execute if false
    """

    def __init__( self, condition: expr.Expr, then_branch: Stmt, else_branch: Stmt) -> None:
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_if_stmt(self)


class Print(Stmt):
    """Represent print statement.

    Parameters
    ----------
    expression : expr.Expr
        Expression to write to stdout
    """

    def __init__(self, expression: expr.Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_print_stmt(self)


class Return(Stmt):
    """Represent return statement.

    Parameters
    ----------
    keyword : tokens.Token
        Token with `return` keyword
    value : expr.Expr
        Value to return from function
    """

    def __init__(self, keyword: tokens.Token, value: expr.Expr) -> None:
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_return_stmt(self)


class Break(Stmt):
    """Represent break statement.

    Parameters
    ----------
    keyword : tokens.Token
        Token with `break` keyword
    """

    def __init__(self, keyword: tokens.Token) -> None:
        self.keyword = keyword

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_break_stmt(self)


class While(Stmt):
    """Represent a loop.

    Parameters
    ----------
    condition : expr.Expr
        Condition to check each iteration of loop
    body : Stmt
        Statement or block of statements to execute each iteration
    """

    def __init__(self, condition: expr.Expr, body: Stmt) -> None:
        self.condition = condition
        self.body = body

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_while_stmt(self)


class Var(Stmt):
    """Represent a variable declaration.

    Variables are stored in a dictionary that allows several items
    because several variables may be declared in a single declaration
    using the comma operator.

    Parameters
    ----------
    variables : dict[tokens.Token, expr.Expr]
        Map of names to values that represent variables
    """

    def __init__(self, variables: dict[tokens.Token, expr.Expr]) -> None:
        self.variables = variables

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_var_stmt(self)
