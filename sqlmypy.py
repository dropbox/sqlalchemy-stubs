from mypy.plugin import Plugin
from mypy.nodes import NameExpr
from mypy.types import UnionType, NoneTyp, Instance


class BasicSQLAlchemyPlugin(Plugin):
    def get_function_hook(self, fullname):
        if fullname == 'sqlalchemy.sql.schema.Column':
            return column_hook
        return None


def column_hook(ctx):
    assert isinstance(ctx.default_return_type, Instance)
    last_arg_exprs = ctx.args[-1]
    if nullable:
        return ctx.default_return_type
    assert len(ctx.default_return_type.args) == 1
    arg_type = ctx.default_return_type.args[0]
    return Instance(ctx.default_return_type.type, [UnionType([arg_type, NoneTyp()])],
                    line=ctx.default_return_type.line,
                    column=ctx.default_return_type.column)


def plugin(version):
    return BasicSQLAlchemyPlugin
