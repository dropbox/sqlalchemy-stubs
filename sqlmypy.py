from mypy.plugin import Plugin
from mypy.nodes import NameExpr, Expression, StrExpr, TypeInfo
from mypy.types import UnionType, NoneTyp, Instance, Type, CallableType, AnyType, TypeOfAny
from mypy.erasetype import erase_typevars

from typing import Optional, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from mypy.plugin import FunctionContext


class BasicSQLAlchemyPlugin(Plugin):
    def get_function_hook(self, fullname: str) -> Optional[Callable[['FunctionContext'], Type]]:
        if fullname == 'sqlalchemy.sql.schema.Column':
            return column_hook
        if fullname == 'sqlalchemy.orm.relationships.RelationshipProperty':
            return relationship_hook
        return None


def relationship_hook(ctx: 'FunctionContext') -> Type:
    assert isinstance(ctx.default_return_type, Instance)
    arg_type = ctx.arg_types[0][0]
    arg = ctx.args[0][0]
    if isinstance(arg_type, CallableType) and arg_type.is_type_obj():
        return Instance(ctx.default_return_type.type, [erase_typevars(arg_type.ret_type)],
                        line=ctx.default_return_type.line,
                        column=ctx.default_return_type.column)
    elif isinstance(arg, StrExpr):
        name = arg.value
        # Private API, but probably needs to be public.
        try:
            sym = ctx.api.lookup_qualified(name)
        except (KeyError, AssertionError):
            return ctx.default_return_type
        if sym and isinstance(sym.node, TypeInfo):
            any = AnyType(TypeOfAny.special_form)
            new_arg = Instance(sym.node, [any] * len(sym.node.defn.type_vars))
            return Instance(ctx.default_return_type.type, [new_arg],
                            line=ctx.default_return_type.line,
                            column=ctx.default_return_type.column)
    return ctx.default_return_type


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
    # TODO: Add support for literal types when they will be available.

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
