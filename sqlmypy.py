from mypy.plugin import Plugin, FunctionContext, ClassDefContext
from mypy.plugins.common import add_method
from mypy.nodes import(
    NameExpr, Expression, StrExpr, TypeInfo, ClassDef, Block, SymbolTable, SymbolTableNode, GDEF,
    Argument, Var, ARG_STAR2
)
from mypy.types import (
    UnionType, NoneTyp, Instance, Type, AnyType, TypeOfAny, UninhabitedType, CallableType
)
from mypy.typevars import fill_typevars_with_any

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


def get_argument_by_name(ctx: FunctionContext, name: str) -> Optional[Expression]:
    """Return the expression for the specific argument.

    This helper should only be used with non-star arguments.
    """
    if name not in ctx.callee_arg_names:
        return None
    idx = ctx.callee_arg_names.index(name)
    args = ctx.args[idx]
    if len(args) != 1:
        # Either an error or no value passed.
        return None
    return args[0]


def get_argtype_by_name(ctx: FunctionContext, name: str) -> Optional[Type]:
    """Same as above but for argument type."""
    if name not in ctx.callee_arg_names:
        return None
    idx = ctx.callee_arg_names.index(name)
    arg_types = ctx.arg_types[idx]
    if len(arg_types) != 1:
        # Either an error or no value passed.
        return None
    return arg_types[0]


def column_hook(ctx: FunctionContext) -> Type:
    """Infer better types for Column calls.

    Examples:
        Column(String) -> Column[Optional[str]]
        Column(String, primary_key=True) -> Column[str]
        Column(String, nullable=False) -> Column[str]
        Column(String, default=...) -> Column[str]
        Column(String, default=..., nullable=True) -> Column[Optional[str]]

    TODO: check the type of 'default'.
    """
    assert isinstance(ctx.default_return_type, Instance)

    nullable_arg = get_argument_by_name(ctx, 'nullable')
    primary_arg = get_argument_by_name(ctx, 'primary_key')
    default_arg = get_argument_by_name(ctx, 'default')

    if nullable_arg:
        nullable = parse_bool(nullable_arg)
    else:
        if primary_arg:
            nullable = not parse_bool(primary_arg)
        else:
            nullable = default_arg is None
    # TODO: Add support for literal types.

    if not nullable:
        return ctx.default_return_type
    assert len(ctx.default_return_type.args) == 1
    arg_type = ctx.default_return_type.args[0]
    return Instance(ctx.default_return_type.type, [UnionType([arg_type, NoneTyp()])],
                    line=ctx.default_return_type.line,
                    column=ctx.default_return_type.column)


def relationship_hook(ctx: FunctionContext) -> Type:
    """Support basic use cases for relationships.

    Examples:
        from sqlalchemy.orm import relationship

        from one import OneModel
        if TYPE_CHECKING:
            from other import OtherModel

        class User(Base):
            __tablename__ = 'users'
            id = Column(Integer(), primary_key=True)
            one = relationship(OneModel)
            other = relationship("OtherModel")

    This also tries to infer the type argument for 'RelationshipProperty'
    using the 'uselist' flag.
    """
    assert isinstance(ctx.default_return_type, Instance)
    original_type_arg = ctx.default_return_type.args[0]
    has_no_annotation = isinstance(original_type_arg, UninhabitedType)

    arg = get_argument_by_name(ctx, 'argument')
    arg_type = get_argtype_by_name(ctx, 'argument')

    uselist_arg = get_argument_by_name(ctx, 'uselist')

    if isinstance(arg, StrExpr):
        name = arg.value
        # Private API for local lookup, but probably needs to be public.
        try:
            sym = ctx.api.lookup_qualified(name)  # type: Optional[SymbolTableNode]
        except (KeyError, AssertionError):
            sym = None
        if sym and isinstance(sym.node, TypeInfo):
            new_arg = fill_typevars_with_any(sym.node)
        else:
            ctx.api.fail('Cannot find model "{}"'.format(name), ctx.context)
            ctx.api.note('Only imported models can be found; use "if TYPE_CHECKING: ..." to avoid import cycles', ctx.context)
            new_arg = AnyType(TypeOfAny.from_error)
    else:
        if isinstance(arg_type, CallableType) and arg_type.is_type_obj():
            new_arg = fill_typevars_with_any(arg_type.type_object())
        else:
            # Something complex, stay silent for now.
            new_arg = AnyType(TypeOfAny.special_form)

    # We figured out, the model type. Now check if we need to wrap it in Iterable
    if uselist_arg:
        if parse_bool(uselist_arg):
            new_arg = ctx.api.named_generic_type('typing.Iterable', [new_arg])
    else:
        if has_no_annotation and not isinstance(new_arg, AnyType):
            ctx.api.fail('Cannot figure out kind of relationship', ctx.context)
            ctx.api.note('Suggestion: use an explicit "uselist" flag', ctx.context)

    return Instance(ctx.default_return_type.type, [new_arg],
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
