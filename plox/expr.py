from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from tokens import Token


R = TypeVar("R")


class Visitor(ABC, Generic[R]):
    """An interface other classes implement to use these types."""

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

    @abstractmethod
    def visit_comma_expr(self, expr: Comma) -> R:
        raise NotImplementedError

    @abstractmethod
    def visit_conditional_expr(self, expr: Conditional) -> R:
        raise NotImplementedError


class Expr(ABC):
    """Abstract class from which all expressions inherit.

    Expressions must implement a method accept() because other classes,
    namely `Interpreter` and `Resolver` use the visitor pattern. This
    pattern allows different classes to implement different behavior for
    the same types without changing the types themselves.
    """

    @abstractmethod
    def accept(self, visitor: Visitor[R]) -> R:
        raise NotImplementedError


class Assign(Expr):
    """Represent assignment expressions.

    Parameters
    ----------
    name : Token
        Token of variable to which to assign the value
    value : Expr
        Expression to evaluate for new value of variable
    """

    def __init__(self, name: Token, value: Expr) -> None:
        self.name = name
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_assign_expr(self)


class Binary(Expr):
    """Represent binary expressions.

    Parameters
    ----------
    left : Expr
        Expression on left-hand side of operand
    operator : Token
        Token of operator that defines the computation
    right : Expr
        Expression on right-hand side of operand
    """

    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_binary_expr(self)


class Call(Expr):
    """Represent call expressions.

    Parameters
    ----------
    callee : Expr
        Expression to evaluate and call
    paren : Token
        Parentheses that signify a call expression
    arguments : list[Expr]
        List of arguments required to call `callee`
    """

    def __init__(self, callee: Expr, paren: Token, arguments: list[Expr]) -> None:
        self.callee = callee
        self.paren = paren
        self.arguments = arguments

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_call_expr(self)


class Get(Expr):
    """Represent an expression that returns a value from an instance.

    Parameters
    ----------
    item : Expr
        Expression to evaluate to instance
    name : Token
        Name of property
    """

    def __init__(self, item: Expr, name: Token) -> None:
        self.item = item
        self.name = name

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_get_expr(self)


class Grouping(Expr):
    """Represent expression surrounded by parentheses.

    Parentheses change order of operations.

    Parameters
    ----------
    expression : Expr
        Expression surrounded by parentheses to evaluate
    """

    def __init__(self, expression: Expr) -> None:
        self.expression = expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    """Represent literal expressions.

    Parameters
    ----------
    value : str | float
        Literal value
    """
    def __init__(self, value: str | float) -> None:
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_literal_expr(self)


class Logical(Expr):
    """Represent logical expressions: `and`, `or`.

    These are a type of binary expression.

    left : Expr
        Expression to the left of the logical operator
    operator : Token
        Token that represents logical operation
    right : Expr
        Expression to the right of the logical operator
    """

    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_logical_expr(self)


class Set(Expr):
    """Represent an expression that sets some value for an instance.

    Parameters
    ----------
    item : Expr
        Expression to evaluate to get instance for which to set value
    name : Token
        Name of property for which to set a value
    value : Expr
        Value to set for the property
    """
    def __init__(self, item: Expr, name: Token, value: Expr) -> None:
        self.item = item
        self.name = name
        self.value = value

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_set_expr(self)


class Super(Expr):
    """Represent `super` expression in a class.

    Parameters
    ----------
    keyword : Token
        Token for `super` keyword
    method : Token
        Method or property following use of `super`
    """

    def __init__(self, keyword: Token, method: Token) -> None:
        self.keyword = keyword
        self.method = method

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_super_expr(self)


class This(Expr):
    """Represent `this` expression.

    Parameters
    ----------
    keyword : TOken
        Token for `this` keyword
    """

    def __init__(self, keyword: Token) -> None:
        self.keyword = keyword

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_this_expr(self)


class Unary(Expr):
    """Represent unary expressions.

    Parameters
    ----------
    operator : Token
        Unary operation to perform
    right : Expr
        Expression on which to perform the operation
    """

    def __init__(self, operator: Token, right: Expr) -> None:
        self.operator = operator
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_unary_expr(self)


class Variable(Expr):
    """Represent variable expression.

    Parameters
    ----------
    name : Token
        Token with name of variable
    """

    def __init__(self, name: Token) -> None:
        self.name = name

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_variable_expr(self)


class Comma(Expr):
    """Represent a comma expression.

    The comma acts as an operator that separates two expressions. In a
    sense, this is also then a binary expression.

    Parameters
    ----------
    left : Expr
        Expression to the left of the comma
    right : Expr
        Expression to the right of the comma
    """

    def __init__(self, left: Expr, right: Expr) -> None:
        self.left = left
        self.right = right

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_comma_expr(self)


class Conditional(Expr):
    """Represent a conditional or ternary expression.

    Parameters
    ----------
    condition : Expr
        Expression to choose then or else
    then_expression : Expr
        Expression to evaluate if `condition` evaluates to true
    else_expression : Expr
        Expression to evaluate if `condition` evaluates to false
    """

    def __init__(self, condition: Expr, then_expression: Expr, else_expression: Expr) -> None:
        self.condition = condition
        self.then_expression = then_expression
        self.else_expression = else_expression

    def accept(self, visitor: Visitor[R]) -> R:
        return visitor.visit_conditional_expr(self)
