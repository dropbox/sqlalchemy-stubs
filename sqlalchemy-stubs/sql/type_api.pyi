from typing import Any, Optional, TypeVar, Generic, Type
from .. import util
from .visitors import Visitable as Visitable, VisitableType as VisitableType
from .base import SchemaEventTarget as SchemaEventTarget
from . import operators
from .sqltypes import NullType, Integer, Boolean, String, MatchType, Indexable

_T = TypeVar('_T')

# TODO: simplify import cycle with sqltypes
BOOLEANTYPE: Boolean = ...
INTEGERTYPE: Integer = ...
NULLTYPE: NullType = ...
STRINGTYPE: String = ...
MATCHTYPE: MatchType = ...
INDEXABLE: Indexable = ...

class TypeEngine(Visitable, Generic[_T]):
    class Comparator(operators.ColumnOperators):
        default_comparator: Any = ...
        expr: Any = ...
        type: Any = ...
        def __init__(self, expr) -> None: ...
        def operate(self, op, *other, **kwargs): ...
        def reverse_operate(self, op, other, **kwargs): ...
        def __reduce__(self): ...
    hashable: bool = ...
    comparator_factory: Any = ...
    should_evaluate_none: bool = ...
    def evaluates_none(self): ...
    def copy(self, **kw): ...
    def compare_against_backend(self, dialect, conn_type): ...
    def copy_value(self, value): ...
    def literal_processor(self, dialect): ...
    def bind_processor(self, dialect): ...
    def result_processor(self, dialect, coltype): ...
    def column_expression(self, colexpr): ...
    def bind_expression(self, bindvalue): ...
    def compare_values(self, x, y): ...
    def get_dbapi_type(self, dbapi): ...
    @property
    def python_type(self) -> Type[_T]: ...
    def with_variant(self, type_, dialect_name): ...
    def dialect_impl(self, dialect): ...
    def adapt(self, *args, **kw): ...
    def coerce_compared_value(self, op, value): ...
    def compile(self, dialect: Optional[Any] = ...): ...

class VisitableCheckKWArg(util.EnsureKWArgType, VisitableType): ...

class UserDefinedType(TypeEngine[_T], metaclass=VisitableCheckKWArg):
    __visit_name__: str = ...
    ensure_kwarg: str = ...
    class Comparator(TypeEngine.Comparator): ...
    comparator_factory: Any = ...
    def coerce_compared_value(self, op, value): ...

class TypeDecorator(SchemaEventTarget, TypeEngine[_T]):
    __visit_name__: str = ...
    impl: Type[TypeEngine[Any]] = ...  # TODO: second type variable? (return of process_bind_param)
    def __init__(self, *args, **kwargs) -> None: ...
    coerce_to_is_types: Any = ...
    class Comparator(TypeEngine.Comparator):
        def operate(self, op, *other, **kwargs): ...
        def reverse_operate(self, op, other, **kwargs): ...
    @property
    def comparator_factory(self): ...
    def type_engine(self, dialect): ...
    def load_dialect_impl(self, dialect): ...
    def __getattr__(self, key): ...
    def process_literal_param(self, value, dialect): ...
    def process_bind_param(self, value, dialect): ...
    def process_result_value(self, value, dialect) -> Optional[_T]: ...
    def literal_processor(self, dialect): ...
    def bind_processor(self, dialect): ...
    def result_processor(self, dialect, coltype): ...
    def coerce_compared_value(self, op, value): ...
    def copy(self, **kw): ...
    def get_dbapi_type(self, dbapi): ...
    def compare_values(self, x, y): ...

class Variant(TypeDecorator[_T]):
    impl: Any = ...
    mapping: Any = ...
    def __init__(self, base: TypeEngine[_T], mapping) -> None: ...
    def coerce_compared_value(self, operator, value): ...
    def load_dialect_impl(self, dialect): ...
    def with_variant(self, type_, dialect_name): ...
    @property
    def comparator_factory(self): ...

def to_instance(typeobj, *arg, **kw): ...
def adapt_type(typeobj, colspecs): ...
