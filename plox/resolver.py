from __future__ import annotations
from enum import auto, IntEnum, unique

import expr
import interpreter
import lox
import stmt
import tokens


class FunctionType(IntEnum):
    NONE = auto()
    FUNCTION = auto()
    METHOD = auto()


class Resolver(expr.Visitor, stmt.Visitor):
    def __init__(self, intrp: interpreter.Interpreter) -> None:
        self.intrp = intrp
        self.scopes: list[dict[str, bool]] = []
        self.current_function = FunctionType.NONE

    def resolve(self, item: list[stmt.Stmt] | stmt.Stmt | expr.Expr) -> None:
        if isinstance(item, list):
            statements = item
            for statement in statements:
                self.resolve(statement)
        elif isinstance(item, stmt.Stmt) or isinstance(item, expr.Expr):
            item.accept(self)
        else:
            raise TypeError

    def resolve_function(self, function: stmt.Function, function_type: FunctionType) -> None:
        enclosing_function = self.current_function
        self.current_function = function_type

        self.begin_scope()
        for parameter in function.params:
            self.declare(parameter)
            self.define(parameter)
        self.resolve(function.body)
        self.end_scope()

        self.current_function = enclosing_function

    def resolve_local(self, expression: expr.Expr, name: tokens.Token) -> None:
        for i in range(len(self.scopes) - 1, -1, -1):
            if name.lexeme in self.scopes[i]:
                self.intrp.resolve(expression, len(self.scopes) - 1 - i)
                return

    def begin_scope(self) -> None:
        self.scopes.append({})

    def end_scope(self) -> None:
        self.scopes.pop()

    def declare(self, name: tokens.Token) -> None:
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]
        if name.lexeme in scope:
            lox.error(name, "a variable with this name already exists in this scope")
        scope[name.lexeme] = False

    def define(self, name: tokens.Token) -> None:
        if len(self.scopes) == 0:
            return
        self.scopes[-1][name.lexeme] = True

    def visit_block_stmt(self, statement: stmt.Block) -> None:
        self.begin_scope()
        self.resolve(statement.statements)
        self.end_scope()

    def visit_class_stmt(self, statement: stmt.Class) -> None:
        self.declare(statement.name)
        for method in statement.methods:
            self.resolve_function(method, FunctionType.METHOD)
        self.define(statement.name)

    def visit_expression_stmt(self, statement: stmt.Expression) -> None:
        self.resolve(statement.expression)

    def visit_if_stmt(self, statement: stmt.If) -> None:
        self.resolve(statement.condition)
        self.resolve(statement.then_branch)
        if statement.else_branch is not None:
            self.resolve(statement.else_branch)

    def visit_print_stmt(self, statement: stmt.Print) -> None:
        self.resolve(statement.expression)

    def visit_return_stmt(self, statement: stmt.Return) -> None:
        if self.current_function == FunctionType.NONE:
            lox.error(statement.keyword, "cannot return from top-level code")

        if statement.value is not None:
            self.resolve(statement.value)

    def visit_while_stmt(self, statement: stmt.While) -> None:
        self.resolve(statement.condition)
        self.resolve(statement.body)

    def visit_function_stmt(self, statement: stmt.Function) -> None:
        self.declare(statement.name)
        self.define(statement.name)
        self.resolve_function(statement, FunctionType.FUNCTION)

    def visit_var_stmt(self, statement: stmt.Var) -> None:
        self.declare(statement.name)
        if statement.initializer is not None:
            self.resolve(statement.initializer)
        self.define(statement.name)

    def visit_assign_expr(self, expression: expr.Assign) -> None:
        self.resolve(expression.value)
        self.resolve_local(expression, expression.name)

    def visit_binary_expr(self, expression: expr.Binary) -> None:
        self.resolve(expression.left)
        self.resolve(expression.right)

    def visit_call_expr(self, expression: expr.Call) -> None:
        self.resolve(expression.callee)
        for argument in expression.arguments:
            self.resolve(argument)

    def visit_get_expr(self, expression: expr.Get) -> None:
        self.resolve(expression.item)

    def visit_grouping_expr(self, expression: expr.Grouping) -> None:
        self.resolve(expression.expression)

    def visit_literal_expr(self, expression: expr.Literal) -> None:
        return

    def visit_logical_expr(self, expression: expr.Logical) -> None:
        self.resolve(expression.left)
        self.resolve(expression.right)

    def visit_set_expr(self, expression: expr.Set) -> None:
        self.resolve(expression.value)
        self.resolve(expression.item)

    def visit_unary_expr(self, expression: expr.Unary) -> None:
        self.resolve(expression.right)

    def visit_variable_expr(self, expression: expr.Variable) -> None:
        if len(self.scopes) and self.scopes[-1].get(expression.name.lexeme) is False:
            lox.error(expression.name, "cannot read local variable in its own initializer")
        self.resolve_local(expression, expression.name)