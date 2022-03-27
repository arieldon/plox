from __future__ import annotations
from dataclasses import dataclass
from enum import auto, IntEnum, unique

import expr
from interpreter import Interpreter
import lox
import stmt
import tokens


@dataclass
class LocalVariableState:
    """Store state when resolving local variables."""
    ready: bool = False
    used: bool = False
    line_number: int = 0


class FunctionType(IntEnum):
    """Specify function type in Resolver."""
    NONE = auto()
    FUNCTION = auto()
    INITIALIZER = auto()
    METHOD = auto()


class ClassType(IntEnum):
    """Specify class type in Resolver."""
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Resolver(expr.Visitor[None], stmt.Visitor[None]):
    """A resolver that manages scope and performs semantic analysis.

    Lox uses lexical or static scope: a variable usage refers to the
    declaration directly before it with the same name within the
    innermost scope, and a variable always resolves to the same
    declaration.

    Consequently, it's possible to resolve each variable once instead of
    allowing the Interpreter to resolve a variable dynamically for each
    use.

    All in all, the resolver locates the declaration to which a local
    variable refers. It produces no side effects, and it does not follow
    control flow. All loops and conditional branches are resolved once.
    Likewise, logical operators are not short-circuited.

    Parameters
    ----------
    interpreter : Interpreter
        An instance of Interpreter

    Arguments
    ---------
    interpreter : Interpreter
        An instance of Interpreter
    scopes : list[dict[str, LocalVariableState]]
        Stack of scopes, where keys of each scope represent variables
        and their corresponding values represent the state of resolution
        of the local variable. As index of list increases, nesting of
        scope increases as well; that is, the last entry in the list
        represents the innermost scope.
    current_function : FunctionType
        Specify current function scope
    current_class : ClassType
        Specify current class scope
    loop_status : bool
        Indicate current scope exists directly within a loop

    Methods
    -------
    resolve() : None
        Resolve variables for given statements

    Notes
    -----
    Declaration and definition are necessary to bind a variable to a
    scope.

    Declaration and definition -- methods declare() and define(),
    respectively -- are split into two separate procedures to prevent
    the reference of a variable in its own initialization. Declaration
    binds the variable to the innermost scope. Definition then indicates
    the variable expression has been resolved.
    """

    def __init__(self, interpreter: Interpreter) -> None:
        self.interpreter = interpreter
        self.scopes: list[dict[str, LocalVariableState]] = []
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE
        self.loop_status = False

    def resolve(self, item: list[stmt.Stmt] | stmt.Stmt | expr.Expr) -> None:
        """Resolve variables for given statements."""
        if isinstance(item, list):
            statements = item
            for statement in statements:
                self.resolve(statement)
        elif isinstance(item, stmt.Stmt) or isinstance(item, expr.Expr):
            item.accept(self)
        else:
            raise TypeError

    def resolve_function(self, function: stmt.Function, function_type: FunctionType) -> None:
        """Create and resolve scope for function declaration.

        A function declaration pushes a new scope onto the stack for its
        body and binds its parameters to this scope.
        """
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
        """Resolve the use of a local variable.

        Begin at innermost scope and progress outward, checking each
        scope for the variable name. If found, pass number of scopes
        from that of the use of the variable to the interpreter. If not
        found, assume the variable is global.
        """
        for i in range(len(self.scopes) - 1, -1, -1):
            if name.lexeme in self.scopes[i]:
                self.scopes[i][name.lexeme].used = True
                self.interpreter.resolve(expression, len(self.scopes) - 1 - i)
                return

    def begin_scope(self) -> None:
        """Create and push new scope onto stack of scopes."""
        self.scopes.append({})

    def end_scope(self) -> None:
        """Remove a used scope from stack of scopes."""
        scope = self.scopes.pop()
        for name, variable_state in scope.items():
            if variable_state.used is False:
                lox.error(variable_state.line_number, f"local variable '{name}' was not used")

    def declare(self, name: tokens.Token) -> None:
        """Add variable to innermost scope.

        Mark variable as declared but undefined with `False` -- it is
        not ready for use.
        """
        if len(self.scopes) == 0:
            return
        scope = self.scopes[-1]
        if name.lexeme in scope:
            lox.error(name, "a variable with this name already exists in this scope")
        scope[name.lexeme] = LocalVariableState(line_number=name.line)

    def define(self, name: tokens.Token) -> None:
        """Indicate a variable is declared, defined, and ready for use.

        Prior to indicating a variable is defined and thus ready for
        use, resolve its initializer expression.

        `True` indicates a variable is available for use.
        """
        if len(self.scopes) == 0:
            return
        self.scopes[-1][name.lexeme].ready = True

    def visit_block_stmt(self, statement: stmt.Block) -> None:
        """Create and resolve new scope for statements within block."""
        self.begin_scope()
        self.resolve(statement.statements)
        self.end_scope()

    def visit_class_stmt(self, statement: stmt.Class) -> None:
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(statement.name)
        self.define(statement.name)

        if statement.superclass is not None:
            if statement.name.lexeme == statement.superclass.name.lexeme:
                lox.error(statement.superclass.name, "a class cannot inherit from itself")
            self.current_class = ClassType.SUBCLASS
            self.resolve(statement.superclass)

            self.begin_scope()
            # A line number is not provided because `super` is declared and defined automatically.
            self.scopes[-1]["super"] = LocalVariableState(ready=True, used=True)

        self.begin_scope()
        # As with `super`, a line number is not provided for `this` since it is
        # declared and defined automatically.
        self.scopes[-1]["this"] = LocalVariableState(ready=True, used=True)

        for method in statement.methods:
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            else:
                declaration = FunctionType.METHOD
            self.resolve_function(method, declaration)

        self.end_scope()
        if statement.superclass is not None:
            self.end_scope()
        self.current_class = enclosing_class

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
            if self.current_function == FunctionType.INITIALIZER:
                lox.error(statement.keyword, "cannot return a value from an initializer")
            self.resolve(statement.value)

    def visit_break_stmt(self, statement: stmt.Break) -> None:
        if not self.loop_status:
            lox.error(statement.keyword, "cannot break from a loop outside of a loop")
        return

    def visit_while_stmt(self, statement: stmt.While) -> None:
        self.loop_status = True
        self.resolve(statement.condition)
        self.resolve(statement.body)
        self.loop_status = False

    def visit_function_stmt(self, statement: stmt.Function) -> None:
        self.declare(statement.name)
        self.define(statement.name)
        self.resolve_function(statement, FunctionType.FUNCTION)

    def visit_var_stmt(self, statement: stmt.Var) -> None:
        for name, initializer in statement.variables.items():
            self.declare(name)
            if initializer is not None:
                self.resolve(initializer)
            self.define(name)

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

    def visit_super_expr(self, expression: expr.Super) -> None:
        if self.current_class == ClassType.NONE:
            lox.error(expression.keyword, "cannot use 'super' outside of a class")
        elif self.current_class != ClassType.SUBCLASS:
            lox.error(expression.keyword, "cannot use 'super' in a class with no superclass")
        self.resolve_local(expression, expression.keyword)

    def visit_this_expr(self, expression: expr.This) -> None:
        if self.current_class == ClassType.NONE:
            lox.error(expression.keyword, "cannot use 'this' outside of a class")
            return
        self.resolve_local(expression, expression.keyword)

    def visit_unary_expr(self, expression: expr.Unary) -> None:
        self.resolve(expression.right)

    def visit_variable_expr(self, expression: expr.Variable) -> None:
        if (
            len(self.scopes) and
            (variable := self.scopes[-1].get(expression.name.lexeme)) and
            variable.ready is False
        ):
            lox.error(expression.name, "cannot use local variable in its own initializer")
        self.resolve_local(expression, expression.name)

    def visit_comma_expr(self, expression: expr.Comma) -> None:
        self.resolve(expression.left)
        self.resolve(expression.right)

    def visit_conditional_expr(self, expression: expr.Conditional) -> None:
        self.resolve(expression.condition)
        self.resolve(expression.then_expression)
        self.resolve(expression.else_expression)
