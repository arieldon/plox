from __future__ import annotations
from abc import ABC, abstractmethod
from time import time
from typing import Any
from types import new_class

import environment
import expr
import lox
import stmt
import tokens


class Interpreter(expr.Visitor, stmt.Visitor):
    def __init__(self) -> None:
        self.global_env = environment.Environment()
        self.local_env: dict[expr.Expr, int] = {}
        self.env = self.global_env

        self.global_env.define(
            "clock",
            type(
                "Clock",
                (LoxCallable,),
                {
                    "arity": lambda _: 0,
                    "call": lambda _, x, y: time() / 1000,
                    "__str__": lambda _: "<native fn>",
                },
            )(),
        )

    def interpret(self, statements: list[stmt.Stmt]) -> None:
        try:
            for statement in statements:
                self.execute(statement)
        except RunningTimeError as error:
            lox.runtime_error(error)

    def evaluate(self, expression: expr.Expr) -> Any:
        return expression.accept(self)

    def execute(self, statement: stmt.Stmt) -> None:
        statement.accept(self)

    def resolve(self, expression: expr.Expr, depth: int) -> None:
        self.local_env[expression] = depth

    def execute_block(
        self, statements: list[None | stmt.Stmt], env: environment.Environment
    ) -> None:
        previous = self.env
        try:
            self.env = env
            for statement in statements:
                if statement:
                    self.execute(statement)
        finally:
            self.env = previous

    def visit_block_stmt(self, statement: stmt.Block) -> None:
        self.execute_block(statement.statements, environment.Environment(self.env))

    def visit_class_stmt(self, statement: stmt.Class) -> None:
        if statement.superclass is not None:
            superclass = self.evaluate(statement.superclass)
            if not isinstance(superclass, LoxClass):
                raise RunningTimeError(statement.superclass.name, "superclass must be a class")
        else:
            superclass = None

        self.env.define(statement.name.lexeme, None)

        methods = {}
        for method in statement.methods:
            methods[method.name.lexeme] = LoxFunction(method, self.env, method.name.lexeme == "init")

        cls = LoxClass(statement.name.lexeme, superclass, methods)
        self.env.assign(statement.name, cls)

    def visit_expression_stmt(self, statement: stmt.Expression) -> None:
        self.evaluate(statement.expression)

    def visit_function_stmt(self, statement: stmt.Function) -> None:
        function = LoxFunction(statement, self.env, False)
        self.env.define(statement.name.lexeme, function)

    def visit_if_stmt(self, statement: stmt.If) -> None:
        if self.is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.then_branch)
        elif statement.else_branch is not None:
            self.execute(statement.else_branch)

    def visit_print_stmt(self, statement: stmt.Print) -> None:
        value = self.evaluate(statement.expression)
        print(self.stringify(value))

    def visit_return_stmt(self, statement: stmt.Return) -> None:
        value = None
        if statement.value is not None:
            value = self.evaluate(statement.value)
        raise Return(value)

    def visit_while_stmt(self, statement: stmt.While) -> None:
        while self.is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.body)

    def visit_var_stmt(self, statement: stmt.Var) -> None:
        value = None
        if statement.initializer:
            value = self.evaluate(statement.initializer)
        self.env.define(statement.name.lexeme, value)

    def visit_assign_expr(self, expression: expr.Assign) -> object:
        value = self.evaluate(expression.value)

        if (distance := self.local_env.get(expression)) is not None:
            self.env.assign_at(distance, expression.name, value)
        else:
            self.global_env.assign(expression.name, value)

        return value

    def visit_binary_expr(self, expression: expr.Binary) -> None | str | float:
        left = self.evaluate(expression.left)
        right = self.evaluate(expression.right)

        match expression.operator.token_type:
            case tokens.TokenType.GREATER:
                self.check_number_operands(expression.operator, left, right)
                return float(left) > float(right)
            case tokens.TokenType.GREATER_EQUAL:
                self.check_number_operands(expression.operator, left, right)
                return float(left) >= float(right)
            case tokens.TokenType.LESSER:
                self.check_number_operands(expression.operator, left, right)
                return float(left) < float(right)
            case tokens.TokenType.LESSER_EQUAL:
                self.check_number_operands(expression.operator, left, right)
                return float(left) <= float(right)
            case tokens.TokenType.BANG_EQUAL:
                return not self.is_equal(left, right)
            case tokens.TokenType.EQUAL_EQUAL:
                return self.is_equal(left, right)
            case tokens.TokenType.MINUS:
                self.check_number_operands(expression.operator, left, right)
                return float(left) - float(right)
            case tokens.TokenType.SLASH:
                self.check_number_operands(expression.operator, left, right)
                return float(left) / float(right)
            case tokens.TokenType.STAR:
                self.check_number_operands(expression.operator, left, right)
                return float(left) * float(right)
            case tokens.TokenType.PLUS if isinstance(left, float) and isinstance(right, float):
                return float(left) + float(right)
            case tokens.TokenType.PLUS if isinstance(left, str) and isinstance(right, str):
                return str(left) + str(right)
            case tokens.TokenType.PLUS:
                # Catch any case for PLUS where operators are not either both
                # numbers or both strings.
                raise RunningTimeError(
                    expression.operator, "operands must be two numbers or two strings"
                )

        # Unreachable
        assert False, "This statement should not be reached."
        return None

    def visit_call_expr(self, expression: expr.Call) -> object:
        callee = self.evaluate(expression.callee)

        arguments = []
        for argument in expression.arguments:
            arguments.append(self.evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise RunningTimeError(expression.paren, "can only call functions and classes")

        if len(arguments) != callee.arity():
            raise RunningTimeError(
                expression.paren,
                f"expected {callee.arity()} arguments, but got {len(arguments)}",
            )
        return callee.call(self, arguments)

    def visit_get_expr(self, expression: expr.Get) -> object:
        item = self.evaluate(expression.item)
        if isinstance(item, LoxInstance):
            return item.get(expression.name)
        raise RunningTimeError(expression.name, "only instances have properties")

    def visit_literal_expr(self, expression: expr.Literal) -> None | str | float:
        return expression.value

    def visit_logical_expr(self, expression: expr.Logical) -> object:
        left = self.evaluate(expression.left)
        if expression.operator.token_type == tokens.TokenType.OR:
            if self.is_truthy(left):
                return left
        else:
            if not self.is_truthy(left):
                return left
        return self.evaluate(expression.right)

    def visit_set_expr(self, expression: expr.Set) -> object:
        item = self.evaluate(expression.item)

        if not isinstance(item, LoxInstance):
            raise RunningTimeError(expression.name, "only instances have fields")

        value = self.evaluate(expression.value)
        item.set(expression.name.lexeme, value)
        return value

    def visit_this_expr(self, expression: expr.This) -> object:
        return self.look_up_variable(expression.keyword, expression)

    def visit_grouping_expr(self, expression: expr.Grouping) -> expr.Expr:
        return expression.expression

    def visit_unary_expr(self, expression: expr.Unary) -> float:
        right = self.evaluate(expression.right)

        match expression.operator.token_type:
            case tokens.TokenType.MINUS:
                self.check_number_operand(expression.operator, right)
                return -float(right)
            case tokens.TokenType.BANG:
                return not self.is_truthy(right)

        # Unreachable
        assert False, "This statement should not be reached."
        return None

    def visit_variable_expr(self, expression: expr.Variable) -> object:
        return self.look_up_variable(expression.name, expression)

    def look_up_variable(self, name: tokens.Token, expression: expr.Expr) -> object:
        if (distance := self.local_env.get(expression)) is not None:
            return self.env.get_at(distance, name.lexeme)
        return self.global_env.get(name)

    def check_number_operand(self, operator: tokens.Token, operand: object) -> None:
        if isinstance(operand, float):
            return
        raise RunningTimeError(operator, "operand must be a number")

    def check_number_operands(
        self, operator: tokens.Token, left: object, right: object
    ) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return
        raise RunningTimeError(operator, "operands must be a number")

    def is_truthy(self, item: object) -> bool:
        if not item:
            return False
        elif isinstance(item, bool):
            return bool(item)
        return True

    def is_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True
        elif a is None:
            return False
        return a == b

    def stringify(self, item: object) -> str:
        if item is None:
            return "nil"

        if isinstance(item, float):
            text = str(item)
            if text.endswith(".0"):
                text = text[:len(text) - 2]
            return text

        return str(item)


class RunningTimeError(RuntimeError):
    def __init__(self, token: tokens.Token, message: str) -> None:
        self.token = token
        self.message = message

    def __str__(self) -> str:
        return f"[line {self.token.line}] {self.message}"


class LoxCallable(ABC):
    @abstractmethod
    def arity(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        raise NotImplementedError


class LoxFunction(LoxCallable):
    def __init__(self, declaration: stmt.Function, closure: environment.Environment, is_initializer: bool) -> None:
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        env = environment.Environment(self.closure)
        for parameter, argument in zip(self.declaration.params, arguments):
            env.define(parameter.lexeme, argument)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except Return as return_value:
            if self.is_initializer:
                return self.closure.get_at(0, "this")
            return return_value.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")

        return None

    def bind(self, instance: LoxInstance) -> LoxFunction:
        env = environment.Environment(self.closure)
        env.define("this", instance)
        return LoxFunction(self.declaration, env, self.is_initializer)

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class LoxClass(LoxCallable):
    def __init__(self, name: str, superclass: LoxClass, methods: dict[str, LoxFunction]) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def arity(self) -> int:
        if (initializer := self.find_method("init")) is None:
            return 0
        return initializer.arity()

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        instance = LoxInstance(self)
        if (initializer := self.find_method("init")) is not None:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def find_method(self, name: str) -> None | LoxFunction:
        if (method := self.methods.get(name)) is not None:
            return method
        elif self.superclass is not None:
            return self.superclass.find_method(name)

    def __str__(self) -> str:
        return self.name


class LoxInstance:
    def __init__(self, cls: LoxClass) -> None:
        self.cls = cls
        self.fields: dict[str, object] = {}

    def get(self, name: tokens.Token) -> object:
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        if (method := self.cls.find_method(name.lexeme)) is not None:
            return method.bind(self)

        raise RunningTimeError(name, f"undefined property '{name.lexeme}'")

    def set(self, name: str, value: object) -> None:
        self.fields[name] = value

    def __str__(self) -> str:
        return f"{self.cls.name} instance"


class Return(RuntimeError):
    def __init__(self, value: object) -> None:
        self.value = value
