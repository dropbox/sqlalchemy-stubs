from mypy.plugin import Plugin
from mypy.nodes import NameExpr, Expression
from mypy.types import UnionType, NoneTyp, Instance, Type

from typing import Optional, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from mypy.plugin import FunctionContext


class BasicSQLAlchemyPlugin(Plugin):
    def get_function_hook(self, fullname: str) -> Optional[Callable[['FunctionContext'], Type]]:
        if fullname == 'sqlalchemy.sql.schema.Column':
            return column_hook
        return None


def column_hook(ctx: 'FunctionContext') -> Type:
    assert isinstance(ctx.default_return_type, Instance)
    # This is very fragile, need to update the plugin API.
    if len(ctx.args) in (5, 6):  # overloads with and without the name
        nullable_index = len(ctx.args) - 2
        primary_index = len(ctx.args) - 3
    else:
        # Something new, give up.
        return ctx.default_return_type

    nullable_args = ctx.args[nullable_index]
    primary_args = ctx.args[primary_index]
    if nullable_args:
        nullable = parse_bool(nullable_args[0])
    else:
        if primary_args:
            nullable = not parse_bool(primary_args[0])
        else:
            nullable = True

    if not nullable:
        return ctx.default_return_type
    assert len(ctx.default_return_type.args) == 1
    arg_type = ctx.default_return_type.args[0]
    return Instance(ctx.default_return_type.type, [UnionType([arg_type, NoneTyp()])],
                    line=ctx.default_return_type.line,
                    column=ctx.default_return_type.column)


# We really need to add this to TypeChecker API
def parse_bool(expr: Expression) -> Optional[bool]:
    if isinstance(expr, NameExpr):
         if expr.fullname == 'builtins.True':
             return True
         if expr.fullname == 'builtins.False':
             return False
    return None


def plugin(version):
    return BasicSQLAlchemyPlugin
