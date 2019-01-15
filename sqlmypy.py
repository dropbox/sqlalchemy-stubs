from mypy.plugin import Plugin, FunctionContext, ClassDefContext
from mypy.plugins.common import add_method
from mypy.nodes import(
    NameExpr, Expression, StrExpr, TypeInfo, ClassDef, Block, SymbolTable, SymbolTableNode, GDEF,
    CallExpr, Argument, Var, ARG_STAR2
)
from mypy.types import (
    UnionType, NoneTyp, Instance, Type, CallableType, AnyType, TypeOfAny, Overloaded
)
from mypy.erasetype import erase_typevars

from typing import Optional, Callable, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from typing_extensions import Final

COLUMN_NAME = 'sqlalchemy.sql.schema.Column'  # type: Final
RELATIONSHIP_NAME = 'sqlalchemy.orm.relationships.RelationshipProperty'  # type: Final


def is_declarative(info: TypeInfo) -> bool:
    """Check if this is a subclass of a declarative base."""
    if info.mro:
        for base in info.mro:
            metadata = base.metadata.get('sqlalchemy')
            if metadata and metadata.get('declarative_base'):
                return True
    return False


def set_declarative(info: TypeInfo) -> None:
    """Record given class as a declarative base."""
    info.metadata.setdefault('sqlalchemy', {})['declarative_base'] = True


class BasicSQLAlchemyPlugin(Plugin):
    """Basic plugin to support simple operations with models.

    Currently supported functionality:
      * Recognize dynamically defined declarative bases.
      * Add an __init__() method to models.
      * Provide better types for 'Column's and 'RelationshipProperty's
        using flags 'primary_key', 'nullable', 'uselist', etc.
    """
    def get_function_hook(self, fullname: str) -> Optional[Callable[[FunctionContext], Type]]:
        if fullname == COLUMN_NAME:
            return column_hook
        if fullname == RELATIONSHIP_NAME:
            return relationship_hook
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            # May be a model instantiation
            if is_declarative(sym.node):
                return model_hook
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
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            if is_declarative(sym.node):
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
    """Add a dummy __init__() to a model and record it is generated.

    Instantiation will be checked more precisely when we inferred types
    (using get_function_hook and model_hook).
    """
    if '__init__' in ctx.cls.info.names:
        # Don't override existing definition.
        return
    typ = AnyType(TypeOfAny.special_form)
    var = Var('kwargs', typ)
    kw_arg = Argument(variable=var, type_annotation=typ, initializer=None, kind=ARG_STAR2)
    add_method(ctx, '__init__', [kw_arg], NoneTyp())
    ctx.cls.info.metadata.setdefault('sqlalchemy', {})['generated_init'] = True


def decl_deco_hook(ctx: ClassDefContext) -> None:
    """Support declaring base class as declarative with a decorator.

    For example:
        from from sqlalchemy.ext.declarative import as_declarative

        @as_declarative
        class Base:
            ...
    """
    set_declarative(ctx.cls.info)


def decl_info_hook(ctx):
    """Support dynamically defining declarative bases.

    For example:
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()
    """
    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)

    info = TypeInfo(SymbolTable(), class_def, ctx.api.cur_mod_id)
    class_def.info = info
    obj = ctx.api.builtin_type('builtins.object')
    info.mro = [info, obj.type]
    info.bases = [obj]
    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))
    set_declarative(info)


def model_hook(ctx: FunctionContext) -> Type:
    """More precise model instantiation check.

    Note: sub-models are not supported.
    Note: this is still not perfect, since the context for inference of
          argument types is 'Any'.
    """
    assert isinstance(ctx.default_return_type, Instance)
    model = ctx.default_return_type.type
    metadata = model.metadata.get('sqlalchemy')
    if not metadata or not metadata.get('generated_init'):
        return ctx.default_return_type

    # Collect column names and types defined in the model
    # TODO: cache this?
    expected_types = {}  # type: Dict[str, Type]
    for name, sym in model.names.items():
        if isinstance(sym.node, Var) and isinstance(sym.node.type, Instance):
            tp = sym.node.type
            if tp.type.fullname() in (COLUMN_NAME, RELATIONSHIP_NAME):
                assert len(tp.args) == 1
                expected_types[name] = tp.args[0]

    assert len(ctx.arg_names) == 1  # only **kwargs in generated __init__
    assert len(ctx.arg_types) == 1
    for actual_name, actual_type in zip(ctx.arg_names[0], ctx.arg_types[0]):
        if actual_name not in expected_types:
            ctx.api.fail('Unexpected column "{}" for model "{}"'.format(actual_name, model.name()),
                         ctx.context)
            continue
        # Using private API to simplify life.
        ctx.api.check_subtype(actual_type, expected_types[actual_name],
                             ctx.context,
                             'Incompatible type for "{}" of "{}"'.format(actual_name, model.name()),
                             'got', 'expected')
    return ctx.default_return_type


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
    # TODO: Add support for literal types.

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
