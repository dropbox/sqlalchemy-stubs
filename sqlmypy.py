from mypy.plugin import Plugin, FunctionContext, ClassDefContext
from mypy.plugins.common import add_method
from mypy.nodes import(
    NameExpr, Expression, StrExpr, TypeInfo, ClassDef, Block, SymbolTable, SymbolTableNode, GDEF,
    AssignmentStmt, CallExpr, RefExpr, Argument, Var, ARG_OPT
)
from mypy.types import (
    UnionType, NoneTyp, Instance, Type, CallableType, AnyType, TypeOfAny, Overloaded
)
from mypy.erasetype import erase_typevars
from mypy.maptype import map_instance_to_supertype

from typing import Optional, Callable, Set, List

DECL_BASES = set()  # type: Set[str]


class BasicSQLAlchemyPlugin(Plugin):
    def get_function_hook(self, fullname: str) -> Optional[Callable[[FunctionContext], Type]]:
        if fullname == 'sqlalchemy.sql.schema.Column':
            return column_hook
        if fullname == 'sqlalchemy.orm.relationships.RelationshipProperty':
            return relationship_hook
        return None

    def get_dynamic_class_hook(self, fullname):
        if fullname == 'sqlalchemy.ext.declarative.api.declarative_base':
            return decl_info_hook
        return None

    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname == 'sqlalchemy.ext.declarative.api.as_declarative':
            return decl_deco_hook
        return None

    def get_base_class_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname in DECL_BASES:
            return add_init_hook
        return None


def _get_column_argument(call: CallExpr, name: str) -> Optional[Expression]:
    """Return the expression for the specific argument."""
    # This is super sketchy.
    callee_node = call.callee.node
    callee_node_type = callee_node.names['__init__'].type
    assert isinstance(callee_node_type, Overloaded)
    if isinstance(call.args[0], StrExpr):
        overload_index = 0
    else:
        overload_index = 1
    callee_type = callee_node_type.items()[overload_index]
    if not callee_type:
        return None

    argument = callee_type.argument_by_name(name)
    if not argument:
        return None
    assert argument.name

    for i, (attr_name, attr_value) in enumerate(zip(call.arg_names, call.args)):
        if argument.pos is not None and not attr_name and i == argument.pos - 1:
            return attr_value
        if attr_name == argument.name:
            return attr_value
    return None


def add_init_hook(ctx: ClassDefContext) -> None:
    if '__init__' in ctx.cls.info.names:
        # Don't override existing definition.
        return
    col_types = []  # type: List[Type]
    col_names = []  # type: List[str]
    engine_info = ctx.api.named_type_or_none('sqlalchemy.sql.type_api.TypeEngine').type
    for stmt in ctx.cls.defs.body:
        if (isinstance(stmt, AssignmentStmt) and isinstance(stmt.lvalues[0], NameExpr) and
                isinstance(stmt.rvalue, CallExpr) and
                isinstance(stmt.rvalue.callee, RefExpr) and
                stmt.rvalue.callee.fullname == 'sqlalchemy.sql.schema.Column'):
            # OK, this is what we a looking for.
            col_names.append(stmt.lvalues[0].name)
            # First try the easy way...
            if isinstance(stmt.type, Instance):
                col_types.append(stmt.type.args[0])
                continue
            # ...otherwise, the hard way (hard because types are not inferred yet,
            # we are in semantic analysis pass)
            typ_arg = _get_column_argument(stmt.rvalue, 'type_')
            if isinstance(typ_arg, RefExpr):
                typ_name = typ_arg.fullname
            elif isinstance(typ_arg, CallExpr) and isinstance(typ_arg.callee, RefExpr):
                typ_name = typ_arg.callee.fullname
            else:
                col_types.append(AnyType(TypeOfAny.special_form))
                continue
            typ = ctx.api.named_type_or_none(typ_name)
            if typ and typ.type.has_base('sqlalchemy.sql.type_api.TypeEngine'):
                # Using maptype at this stage is dangerous, since if there is an import cycle,
                # the result is unpredictable.
                engine = map_instance_to_supertype(typ, engine_info)
                if engine.args and isinstance(engine.args[0], Instance):
                    # OK, the column type already analyzed, we are good to go
                    col_types.append(engine.args[0])
                    continue
            # Can't figure out type, fall back to Any
            col_types.append(AnyType(TypeOfAny.special_form))
    init_args = []  # type: List[Argument]
    for typ, name in zip(col_types, col_names):
        typ = UnionType([typ, NoneTyp()])
        var = Var(name, typ)
        i_arg = Argument(variable=var, type_annotation=typ, initializer=None, kind=ARG_OPT)
        init_args.append(i_arg)
    add_method(ctx, '__init__', init_args, NoneTyp())


def decl_deco_hook(ctx: ClassDefContext) -> None:
    DECL_BASES.add(ctx.cls.fullname)


def decl_info_hook(ctx):
    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)

    info = TypeInfo(SymbolTable(), class_def, ctx.api.cur_mod_id)
    class_def.info = info
    obj = ctx.api.builtin_type('builtins.object')
    info.mro = [info, obj.type]
    info.bases = [obj]
    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))
    DECL_BASES.add(class_def.fullname)


def relationship_hook(ctx: FunctionContext) -> Type:
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


def column_hook(ctx: FunctionContext) -> Type:
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
