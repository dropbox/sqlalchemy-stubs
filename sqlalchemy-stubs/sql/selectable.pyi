from typing import Any, Optional, TypeVar, Set
from .elements import ClauseElement as ClauseElement, Grouping as Grouping, UnaryExpression as UnaryExpression
from .base import Immutable as Immutable, Executable as Executable, Generative as Generative, ImmutableColumnCollection, ColumnSet
from .annotation import Annotated as Annotated

def subquery(alias, *args, **kwargs): ...
def alias(selectable, name: Optional[Any] = ..., flat: bool = ...): ...
def lateral(selectable, name: Optional[Any] = ...): ...
def tablesample(selectable, sampling, name: Optional[Any] = ..., seed: Optional[Any] = ...): ...

class Selectable(ClauseElement):
    __visit_name__: str = ...
    is_selectable: bool = ...
    @property
    def selectable(self): ...

_HP = TypeVar('_HP', bound=HasPrefixes)

class HasPrefixes(object):
    def prefix_with(self: _HP, *expr, **kw) -> _HP: ...

_HS = TypeVar('_HS', bound=HasSuffixes)

class HasSuffixes(object):
    def suffix_with(self: _HS, *expr, **kw) -> _HS: ...

class FromClause(Selectable):
    __visit_name__: str = ...
    named_with_column: bool = ...
    schema: Any = ...
    def count(self, whereclause: Optional[Any] = ..., **params) -> Select: ...
    def select(self, whereclause: Optional[Any] = ..., **params) -> Select: ...
    def join(self, right, onclause: Optional[Any] = ..., isouter: bool = ..., full: bool = ...) -> Join: ...
    def outerjoin(self, right, onclause: Optional[Any] = ..., full: bool = ...) -> Join: ...
    def alias(self, name: Optional[Any] = ..., flat: bool = ...) -> Alias: ...
    def lateral(self, name: Optional[Any] = ...) -> Lateral: ...
    def tablesample(self, sampling, name: Optional[Any] = ..., seed: Optional[Any] = ...) -> TableSample: ...
    def is_derived_from(self, fromclause) -> bool: ...
    def replace_selectable(self, old, alias): ...
    def correspond_on_equivalents(self, column, equivalents): ...
    def corresponding_column(self, column, require_embedded: bool = ...): ...
    @property
    def description(self) -> str: ...
    @property
    def columns(self) -> ImmutableColumnCollection: ...
    @property
    def primary_key(self) -> ColumnSet: ...
    @property
    def foreign_keys(self) -> Set[FromClause]: ...
    c: ImmutableColumnCollection = ...

class Join(FromClause):
    __visit_name__: str = ...
    left: Any = ...
    right: Any = ...
    onclause: Any = ...
    isouter: Any = ...
    full: Any = ...
    def __init__(self, left, right, onclause: Optional[Any] = ..., isouter: bool = ..., full: bool = ...) -> None: ...
    @property
    def description(self): ...
    def is_derived_from(self, fromclause): ...
    def self_group(self, against: Optional[Any] = ...): ...
    def get_children(self, **kwargs): ...
    def select(self, whereclause: Optional[Any] = ..., **kwargs): ...
    @property
    def bind(self): ...
    def alias(self, *args, **kwargs): ...
    @classmethod
    def _create_outerjoin(cls, left, right, onclause: Optional[Any] = ..., full: bool = ...) -> Join: ...
    @classmethod
    def _create_join(cls, left, right, onclause: Optional[Any] = ..., isouter: bool = ...,
                     full: bool = ...) -> Join: ...

class Alias(FromClause):
    __visit_name__: str = ...
    named_with_column: bool = ...
    original: Any = ...
    supports_execution: Any = ...
    element: Any = ...
    name: Any = ...
    def __init__(self, selectable, name: Optional[Any] = ...) -> None: ...
    def self_group(self, target: Optional[Any] = ...): ...
    @property
    def description(self): ...
    def as_scalar(self): ...
    def is_derived_from(self, fromclause): ...
    def get_children(self, column_collections: bool = ..., **kw): ...
    @property
    def bind(self): ...

class Lateral(Alias):
    __visit_name__: str = ...

class TableSample(Alias):
    __visit_name__: str = ...
    sampling: Any = ...
    seed: Any = ...
    def __init__(self, selectable, sampling, name: Optional[Any] = ..., seed: Optional[Any] = ...) -> None: ...

class CTE(Generative, HasSuffixes, Alias):
    __visit_name__: str = ...
    recursive: Any = ...
    def __init__(self, selectable, name: Optional[Any] = ..., recursive: bool = ...,
                 _cte_alias: Optional[Any] = ..., _restates: Any = ..., _suffixes: Optional[Any] = ...) -> None: ...
    def alias(self, name: Optional[Any] = ..., flat: bool = ...) -> CTE: ...
    def union(self, other) -> CTE: ...
    def union_all(self, other) -> CTE: ...

class HasCTE(object):
    def cte(self, name: Optional[Any] = ..., recursive: bool = ...) -> CTE: ...

class FromGrouping(FromClause):
    __visit_name__: str = ...
    element: Any = ...
    def __init__(self, element) -> None: ...
    @property
    def columns(self) -> ImmutableColumnCollection: ...
    @property
    def primary_key(self) -> ColumnSet: ...
    @property
    def foreign_keys(self) -> Set[FromClause]: ...
    def is_derived_from(self, element): ...
    def alias(self, **kw): ...
    def get_children(self, **kwargs): ...
    def __getattr__(self, attr): ...

class TableClause(Immutable, FromClause):
    __visit_name__: str = ...
    named_with_column: bool = ...
    implicit_returning: bool = ...
    name: Any = ...
    primary_key: ColumnSet = ...
    foreign_keys: Set[FromClause] = ...
    def __init__(self, name, *columns) -> None: ...
    @property
    def description(self): ...
    def append_column(self, c): ...
    def get_children(self, **kwargs): ...
    def insert(self, values: Optional[Any] = ..., inline: bool = ..., **kwargs): ...
    def update(self, whereclause: Optional[Any] = ..., values: Optional[Any] = ..., inline: bool = ...,
               **kwargs): ...
    def delete(self, whereclause: Optional[Any] = ..., **kwargs): ...

class ForUpdateArg(ClauseElement):
    @classmethod
    def parse_legacy_select(self, arg): ...
    @property
    def legacy_for_update_value(self): ...
    nowait: Any = ...
    read: Any = ...
    skip_locked: Any = ...
    key_share: Any = ...
    of: Any = ...
    def __init__(self, nowait: bool = ..., read: bool = ..., of: Optional[Any] = ...,
                 skip_locked: bool = ..., key_share: bool = ...) -> None: ...

_SB = TypeVar('_SB', bound=SelectBase)

class SelectBase(HasCTE, Executable, FromClause):
    def as_scalar(self): ...
    def label(self, name): ...
    def autocommit(self: _SB) -> _SB: ...

_GS = TypeVar('_GS', bound=GenerativeSelect)

class GenerativeSelect(SelectBase):
    use_labels: Any = ...
    def __init__(self, use_labels: bool = ..., for_update: bool = ..., limit: Optional[Any] = ...,
                 offset: Optional[Any] = ..., order_by: Optional[Any] = ...,
                 group_by: Optional[Any] = ..., bind: Optional[Any] = ..., autocommit: Optional[Any] = ...) -> None: ...
    @property
    def for_update(self): ...
    @for_update.setter
    def for_update(self, value): ...
    def with_for_update(self: _GS, nowait: bool = ..., read: bool = ..., of: Optional[Any] = ...,
                        skip_locked: bool = ..., key_share: bool = ...) -> _GS: ...
    def apply_labels(self: _GS) -> _GS: ...
    def limit(self: _GS, limit) -> _GS: ...
    def offset(self: _GS, offset) -> _GS: ...
    def order_by(self: _GS, *clauses) -> _GS: ...
    def group_by(self: _GS, *clauses) -> _GS: ...
    def append_order_by(self, *clauses): ...
    def append_group_by(self, *clauses): ...

class CompoundSelect(GenerativeSelect):
    __visit_name__: str = ...
    UNION: Any = ...
    UNION_ALL: Any = ...
    EXCEPT: Any = ...
    EXCEPT_ALL: Any = ...
    INTERSECT: Any = ...
    INTERSECT_ALL: Any = ...
    keyword: Any = ...
    selects: Any = ...
    def __init__(self, keyword, *selects, **kwargs) -> None: ...
    def self_group(self, against: Optional[Any] = ...): ...
    def is_derived_from(self, fromclause): ...
    def get_children(self, column_collections: bool = ..., **kwargs): ...
    def bind(self): ...
    @classmethod
    def _create_union(cls, *selects, **kwargs) -> CompoundSelect: ...
    @classmethod
    def _create_union_all(cls, *selects, **kwargs) -> CompoundSelect: ...
    @classmethod
    def _create_except(cls, *selects, **kwargs) -> CompoundSelect: ...
    @classmethod
    def _create_except_all(cls, *selects, **kwargs) -> CompoundSelect: ...
    @classmethod
    def _create_intersect(cls, *selects, **kwargs) -> CompoundSelect: ...
    @classmethod
    def _create_intersect_all(cls, *selects, **kwargs) -> CompoundSelect: ...

_S = TypeVar('_S', bound=Select)

class Select(HasPrefixes, HasSuffixes, GenerativeSelect):
    __visit_name__: str = ...
    def __init__(self, columns: Optional[Any] = ..., whereclause: Optional[Any] = ...,
                 from_obj: Optional[Any] = ..., distinct: bool = ..., having: Optional[Any] = ...,
                 correlate: bool = ..., prefixes: Optional[Any] = ..., suffixes: Optional[Any] = ...,
                 **kwargs) -> None: ...
    @property
    def froms(self): ...
    def with_statement_hint(self, text, dialect_name: str = ...): ...
    def with_hint(self: _S, selectable, text, dialect_name: str = ...) -> _S: ...
    @property
    def type(self): ...
    @property
    def locate_all_froms(self): ...
    @property
    def inner_columns(self): ...
    def is_derived_from(self, fromclause): ...
    def get_children(self, column_collections: bool = ..., **kwargs): ...
    def column(self: _S, column) -> _S: ...
    def reduce_columns(self, only_synonyms: bool = ...): ...
    def with_only_columns(self: _S, columns): ...
    def where(self: _S, whereclause) -> _S: ...
    def having(self: _S, having) -> _S: ...
    def distinct(self: _S, *expr) -> _S: ...
    def select_from(self: _S, fromclause) -> _S: ...
    def correlate(self: _S, *fromclauses) -> _S: ...
    def correlate_except(self: _S, *fromclauses) -> _S: ...
    def append_correlation(self, fromclause): ...
    def append_column(self, column): ...
    def append_prefix(self, clause): ...
    def append_whereclause(self, whereclause): ...
    def append_having(self, having): ...
    def append_from(self, fromclause): ...
    def self_group(self, against: Optional[Any] = ...): ...
    def union(self, other, **kwargs): ...
    def union_all(self, other, **kwargs): ...
    def except_(self, other, **kwargs): ...
    def except_all(self, other, **kwargs): ...
    def intersect(self, other, **kwargs): ...
    def intersect_all(self, other, **kwargs): ...
    def bind(self): ...

_SS = TypeVar('_SS', bound=ScalarSelect)

class ScalarSelect(Generative, Grouping):
    element: Any = ...
    type: Any = ...
    def __init__(self, element) -> None: ...
    @property
    def columns(self): ...
    c: Any = ...
    def where(self: _SS, crit) -> _SS: ...
    def self_group(self, **kwargs): ...

class Exists(UnaryExpression):
    __visit_name__: Any = ...
    def __init__(self, *args, **kwargs) -> None: ...
    def select(self, whereclause: Optional[Any] = ..., **params): ...
    def correlate(self, *fromclause): ...
    def correlate_except(self, *fromclause): ...
    def select_from(self, clause): ...
    def where(self, clause): ...

_TAF = TypeVar('_TAF', bound=TextAsFrom)

class TextAsFrom(SelectBase):
    __visit_name__: str = ...
    element: Any = ...
    column_args: Any = ...
    positional: Any = ...
    def __init__(self, text, columns, positional: bool = ...) -> None: ...
    def bindparams(self: _TAF, *binds, **bind_as_values) -> _TAF: ...

class AnnotatedFromClause(Annotated):
    def __init__(self, element, values) -> None: ...
