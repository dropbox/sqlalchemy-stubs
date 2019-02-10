from mypy.mro import calculate_mro, MroError
from mypy.plugin import (
    Plugin, FunctionContext, ClassDefContext, DynamicClassDefContext,
    SemanticAnalyzerPluginInterface
)
from mypy.plugins.common import add_method, _get_argument
from mypy.nodes import (
    NameExpr, Expression, StrExpr, TypeInfo, ClassDef, Block, SymbolTable, SymbolTableNode, GDEF,
    Argument, Var, ARG_STAR2, MDEF, TupleExpr, RefExpr, AssignmentStmt, CallExpr, MemberExpr
)
from mypy.types import (
    UnionType, NoneTyp, Instance, Type, AnyType, TypeOfAny, UninhabitedType, CallableType
)
from mypy.typevars import fill_typevars_with_any

from typing import Optional, Callable, Dict, TYPE_CHECKING, List, Type as TypingType, TypeVar
if TYPE_CHECKING:
    from typing_extensions import Final

T = TypeVar('T')
CB = Optional[Callable[[T], None]]

COLUMN_NAME = 'sqlalchemy.sql.schema.Column'  # type: Final
CLAUSE_ELEMENT_NAME = 'sqlalchemy.sql.elements.ClauseElement'  # type: Final
COLUMN_ELEMENT_NAME = 'sqlalchemy.sql.elements.ColumnElement'  # type: Final
GROUPING_NAME = 'sqlalchemy.sql.elements.Grouping'  # type: Final
RELATIONSHIP_NAME = 'sqlalchemy.orm.relationships.RelationshipProperty'  # type: Final
FOREIGN_KEY_NAME = 'sqlalchemy.sql.schema.ForeignKey'  # type: Final


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
        if fullname == GROUPING_NAME:
            return grouping_hook
        if fullname == RELATIONSHIP_NAME:
            return relationship_hook
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            # May be a model instantiation
            if is_declarative(sym.node):
                return model_hook
        return None

    def get_dynamic_class_hook(self, fullname: str):
        if fullname == 'sqlalchemy.ext.declarative.api.declarative_base':
            return decl_info_hook
        return None

    def get_class_decorator_hook(self, fullname: str):
        if fullname == 'sqlalchemy.ext.declarative.api.as_declarative':
            return decl_deco_hook
        return None

    def get_base_class_hook(self, fullname: str):
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            if is_declarative(sym.node):
                return add_model_init_hook
        return None


def add_var_to_class(name: str, typ: Type, info: TypeInfo) -> None:
    """Add a variable with given name and type to the symbol table of a class.

    This also takes care about setting necessary attributes on the variable node.
    """
    var = Var(name)
    var.info = info
    var._fullname = info.fullname() + '.' + name
    var.type = typ
    info.names[name] = SymbolTableNode(MDEF, var)


def add_model_init_hook(ctx: ClassDefContext) -> None:
    """Add a dummy __init__() to a model and record it is generated.

    Instantiation will be checked more precisely when we inferred types
    (using get_function_hook and model_hook).
    """
    if '__init__' in ctx.cls.info.names:
        # Don't override existing definition.
        return
    any = AnyType(TypeOfAny.special_form)
    var = Var('kwargs', any)
    kw_arg = Argument(variable=var, type_annotation=any, initializer=None, kind=ARG_STAR2)
    add_method(ctx, '__init__', [kw_arg], NoneTyp())
    ctx.cls.info.metadata.setdefault('sqlalchemy', {})['generated_init'] = True

    for stmt in ctx.cls.defs.body:
        if not (isinstance(stmt, AssignmentStmt) and len(stmt.lvalues) == 1 and isinstance(stmt.lvalues[0], NameExpr)):
            continue

        # We currently only handle setting __tablename__ as a class attribute, and not through a property.
        if stmt.lvalues[0].name == "__tablename__" and isinstance(stmt.rvalue, StrExpr):
            ctx.cls.info.metadata.setdefault('sqlalchemy', {})['table_name'] = stmt.rvalue.value

        if isinstance(stmt.rvalue, CallExpr) and stmt.rvalue.callee.fullname == COLUMN_NAME:
            # Save columns. The name of a column on the db side can be different from the one inside the SA model.
            sa_column_name = stmt.lvalues[0].name

            db_column_name = None  # type: Optional[str]
            if 'name' in stmt.rvalue.arg_names:
                name_str_expr = stmt.rvalue.args[stmt.rvalue.arg_names.index('name')]
                assert isinstance(name_str_expr, StrExpr)
                db_column_name = name_str_expr.value
            else:
                if len(stmt.rvalue.args) >= 1 and isinstance(stmt.rvalue.args[0], StrExpr):
                    db_column_name = stmt.rvalue.args[0].value

            ctx.cls.info.metadata.setdefault('sqlalchemy', {}).setdefault('columns', []).append(
                {"sa_name": sa_column_name, "db_name": db_column_name or sa_column_name}
            )

            # Save foreign keys.
            for arg in stmt.rvalue.args:
                if isinstance(arg, CallExpr) and arg.callee.fullname == FOREIGN_KEY_NAME and len(arg.args) >= 1:
                    fk = arg.args[0]
                    if isinstance(fk, StrExpr):
                        *r, parent_table_name, parent_db_col_name = fk.value.split(".")
                        assert len(r) <= 1
                        ctx.cls.info.metadata.setdefault('sqlalchemy', {}).setdefault('foreign_keys',
                                                                                      {})[sa_column_name] = {
                            "db_name": parent_db_col_name,
                            "table_name": parent_table_name,
                            "schema": r[0] if r else None
                        }
                    elif isinstance(fk, MemberExpr):
                        ctx.cls.info.metadata.setdefault('sqlalchemy', {}).setdefault('foreign_keys',
                                                                                      {})[sa_column_name] = {
                            "sa_name": fk.name,
                            "model_fullname": fk.expr.fullname
                        }

    # Also add a selection of auto-generated attributes.
    sym = ctx.api.lookup_fully_qualified_or_none('sqlalchemy.sql.schema.Table')
    if sym:
        assert isinstance(sym.node, TypeInfo)
        typ = Instance(sym.node, [])  # type: Type
    else:
        typ = AnyType(TypeOfAny.special_form)
    add_var_to_class('__table__', typ, ctx.cls.info)


def add_metadata_var(api: SemanticAnalyzerPluginInterface, info: TypeInfo) -> None:
    """Add .metadata attribute to a declarative base."""
    sym = api.lookup_fully_qualified_or_none('sqlalchemy.sql.schema.MetaData')
    if sym:
        assert isinstance(sym.node, TypeInfo)
        typ = Instance(sym.node, [])  # type: Type
    else:
        typ = AnyType(TypeOfAny.special_form)
    add_var_to_class('metadata', typ, info)


def decl_deco_hook(ctx: ClassDefContext) -> None:
    """Support declaring base class as declarative with a decorator.

    For example:
        from from sqlalchemy.ext.declarative import as_declarative

        @as_declarative
        class Base:
            ...
    """
    set_declarative(ctx.cls.info)
    add_metadata_var(ctx.api, ctx.cls.info)


def decl_info_hook(ctx: DynamicClassDefContext) -> None:
    """Support dynamically defining declarative bases.

    For example:
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()
    """
    cls_bases = []  # type: List[Instance]

    # Passing base classes as positional arguments is currently not handled.
    if 'cls' in ctx.call.arg_names:
        declarative_base_cls_arg = ctx.call.args[ctx.call.arg_names.index("cls")]
        if isinstance(declarative_base_cls_arg, TupleExpr):
            items = [item for item in declarative_base_cls_arg.items]
        else:
            items = [declarative_base_cls_arg]

        for item in items:
            if isinstance(item, RefExpr) and isinstance(item.node, TypeInfo):
                base = fill_typevars_with_any(item.node)
                # TODO: Support tuple types?
                if isinstance(base, Instance):
                    cls_bases.append(base)

    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)

    info = TypeInfo(SymbolTable(), class_def, ctx.api.cur_mod_id)
    class_def.info = info
    obj = ctx.api.builtin_type('builtins.object')
    info.bases = cls_bases or [obj]
    try:
        calculate_mro(info)
    except MroError:
        ctx.api.fail("Not able to calculate MRO for declarative base", ctx.call)
        info.bases = [obj]
        info.fallback_to_any = True

    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))
    set_declarative(info)

    # TODO: check what else is added.
    add_metadata_var(ctx.api, info)


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
        if actual_name is None:
            # We can't check kwargs reliably.
            # TODO: support TypedDict?
            continue
        if actual_name not in expected_types:
            ctx.api.fail('Unexpected column "{}" for model "{}"'.format(actual_name,
                                                                        model.name()),
                         ctx.context)
            continue
        # Using private API to simplify life.
        ctx.api.check_subtype(actual_type, expected_types[actual_name],  # type: ignore
                              ctx.context,
                              'Incompatible type for "{}" of "{}"'.format(actual_name,
                                                                          model.name()),
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


def grouping_hook(ctx: FunctionContext) -> Type:
    """Infer better types for Grouping calls.

    Examples:
        Grouping(text('asdf')) -> Grouping[None]
        Grouping(Column(String), nullable=False) -> Grouping[str]
        Grouping(Column(String)) -> Grouping[Optional[str]]
    """
    assert isinstance(ctx.default_return_type, Instance)

    element_arg_type = get_argtype_by_name(ctx, 'element')

    if element_arg_type is not None and isinstance(element_arg_type, Instance):
        if element_arg_type.type.has_base(CLAUSE_ELEMENT_NAME) and not \
                element_arg_type.type.has_base(COLUMN_ELEMENT_NAME):
            return ctx.default_return_type.copy_modified(args=[NoneTyp()])
    return ctx.default_return_type


class IncompleteModelMetadata(Exception):
    pass


def has_foreign_keys(local_model: TypeInfo, remote_model: TypeInfo) -> bool:
    """Tells if `local_model` has a fk to `remote_model`.
    Will raise an `IncompleteModelMetadata` if some mandatory metadata is missing.
    """
    local_metadata = local_model.metadata.get("sqlalchemy", {})
    remote_metadata = remote_model.metadata.get("sqlalchemy", {})

    for fk in local_metadata.get("foreign_keys", {}).values():
        if 'model_fullname' in fk and remote_model.fullname == fk['model_fullname']:
            return True
        if 'table_name' in fk:
            if 'table_name' not in remote_metadata:
                raise IncompleteModelMetadata
            # TODO: handle different schemas
            if remote_metadata['table_name'] == fk['table_name']:
                return True

    return False


def is_relationship_iterable(ctx: FunctionContext, local_model: TypeInfo, remote_model: TypeInfo) -> bool:
    """Tries to guess if the relationship is onetoone/onetomany/manytoone.

    Currently we handle the most current case, where a model relates to the other one through a relationship.
    We also handle cases where secondaryjoin argument is provided.
    We don't handle advanced usecases (foreign keys on both sides, primaryjoin, etc.).
    """
    secondaryjoin = get_argument_by_name(ctx, 'secondaryjoin')

    if secondaryjoin is not None:
        return True

    try:
        can_be_many_to_one = has_foreign_keys(local_model, remote_model)
        can_be_one_to_many = has_foreign_keys(remote_model, local_model)

        if not can_be_many_to_one and can_be_one_to_many:
            return True
    except IncompleteModelMetadata:
        pass

    return False  # Assume relationship is not iterable, if we weren't able to guess better.


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
    has_annotation = not isinstance(original_type_arg, UninhabitedType)

    arg = get_argument_by_name(ctx, 'argument')
    arg_type = get_argtype_by_name(ctx, 'argument')

    uselist_arg = get_argument_by_name(ctx, 'uselist')

    if isinstance(arg, StrExpr):
        name = arg.value
        sym = None  # type: Optional[SymbolTableNode]
        try:
            # Private API for local lookup, but probably needs to be public.
            sym = ctx.api.lookup_qualified(name)  # type: ignore
        except (KeyError, AssertionError):
            pass
        if sym and isinstance(sym.node, TypeInfo):
            new_arg = fill_typevars_with_any(sym.node)  # type: Type
        else:
            ctx.api.fail('Cannot find model "{}"'.format(name), ctx.context)
            # TODO: Add note() to public API.
            ctx.api.note('Only imported models can be found;'  # type: ignore
                         ' use "if TYPE_CHECKING: ..." to avoid import cycles',
                         ctx.context)
            new_arg = AnyType(TypeOfAny.from_error)
    else:
        if isinstance(arg_type, CallableType) and arg_type.is_type_obj():
            new_arg = fill_typevars_with_any(arg_type.type_object())
        else:
            # Something complex, stay silent for now.
            new_arg = AnyType(TypeOfAny.special_form)

    current_model = ctx.api.scope.active_class()
    assert current_model is not None

    # TODO: handle backref relationships

    # We figured out, the model type. Now check if we need to wrap it in Iterable
    if uselist_arg:
        if parse_bool(uselist_arg):
            new_arg = ctx.api.named_generic_type('typing.Iterable', [new_arg])
    elif not isinstance(new_arg, AnyType) and is_relationship_iterable(ctx, current_model, new_arg.type):
        new_arg = ctx.api.named_generic_type('typing.Iterable', [new_arg])
    else:
        if has_annotation:
            # If there is an annotation we use it as a source of truth.
            # This will cause false negatives, but it is better than lots of false positives.
            new_arg = original_type_arg

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


def plugin(version: str) -> TypingType[Plugin]:
    return BasicSQLAlchemyPlugin
