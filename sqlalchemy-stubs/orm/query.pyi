from typing import Any, Optional
from . import interfaces
from .base import InspectionAttr
from .session import Session
from ..sql.selectable import ForUpdateArg, Select

class Query(object):
    session: Session = ...

    def __clause_element__(self): ...
    def __getitem__(self, item): ...
    def __init__(self, entities: Sequence[Any], session: Optional[Session] = ...) -> None: ...
    def __iter__(self): ...
    def add_column(self, column) -> Query: ...
    def add_columns(self, *column) -> Query: ...
    def add_entity(self, entity, alias: Optional[Any] = ...) -> Query: ...
    def all(self): ...
    def as_scalar(self): ...
    def autoflush(self, setting: bool) -> Query: ...
    @property
    def column_descriptions(self): ...
    def correlate(self, *args) -> Query: ...
    def count(self): ...
    def cte(self, name: Optional[Any] = ..., recursive: bool = ...): ...
    def delete(self, synchronize_session: str = ...): ...
    def distinct(self, *criterion) -> Query: ...
    def enable_assertions(self, value) -> Query: ...
    def enable_eagerloads(self, value) -> Query: ...
    def except_(self, *q): ...
    def except_all(self, *q): ...
    def execution_options(self, **kwargs) -> Query: ...
    def exists(self): ...
    def filter(self, *criterion) -> Query: ...
    def filter_by(self, **kwargs): ...
    def first(self): ...
    def from_self(self, *entities): ...
    def from_statement(self, statement) -> Query: ...
    def get(self, ident): ...
    def group_by(self, *criterion) -> Query: ...
    def having(self, criterion) -> Query: ...
    def instances(self, cursor, __context: Optional[Any] = ...): ...
    def intersect(self, *q): ...
    def intersect_all(self, *q): ...
    def join(self, *props, **kwargs): ...
    def label(self, name): ...
    def limit(self, limit: int) -> Query: ...
    def merge_result(self, iterator, load: bool = ...): ...
    def offset(self, offset: int) -> Query: ...
    def one(self): ...
    def one_or_none(self): ...
    def options(self, *args): ...
    def order_by(self, *criterion) -> Query: ...
    def outerjoin(self, *props, **kwargs): ...
    def params(self, *args, **kwargs) -> Query: ...
    def populate_existing(self) -> Query: ...
    def prefix_with(self, *prefixes) -> Query: ...
    def reset_joinpoint(self) -> Query: ...
    def scalar(self): ...
    def select_entity_from(self, from_obj) -> Query: ...
    def select_from(self, *from_obj) -> Query: ...
    @property
    def selectable(self) -> Select: ...
    def slice(self, start: int, stop: int) -> Query: ...
    @property
    def statement(self): ...
    def subquery(self, name: Optional[Any] = ..., with_labels: bool = ..., reduce_columns: bool = ...): ...
    def suffix_with(self, *suffixes) -> Query: ...
    def union(self, *q): ...
    def union_all(self, *q): ...
    def update(self, values, synchronize_session: str = ..., update_args: Optional[Any] = ...): ...
    def value(self, column): ...
    def values(self, *columns): ...
    @property
    def whereclause(self): ...
    def with_entities(self, *entities) -> Query: ...
    def with_for_update(self, read: bool = ..., nowait: bool = ..., of: Optional[Any] = ...,
                        skip_locked: bool = ..., key_share: bool = ...) -> Query: ...
    def with_hint(self, selectable, text, dialect_name: str = ...) -> Query: ...
    def with_labels(self) -> Query: ...
    def with_lockmode(self, mode: Optional[str]) -> Query: ...
    def with_parent(self, instance, property: Optional[Any] = ...): ...
    def with_polymorphic(self, cls_or_mappers, selectable: Optional[Any] = ...,
                         polymorphic_on: Optional[Any] = ...) -> Query: ...
    def with_session(self, session: Session) -> Query: ...
    def with_statement_hint(self, text, dialect_name: str = ...): ...
    def with_transformation(self, fn): ...
    def yield_per(self, count) -> Query: ...


class LockmodeArg(ForUpdateArg):
    @classmethod
    def parse_legacy_query(self, mode): ...

class _QueryEntity(object):
    def __new__(cls, *args, **kwargs): ...

class _MapperEntity(_QueryEntity):
    entities: Any = ...
    expr: Any = ...
    def __init__(self, query, entity) -> None: ...
    supports_single_entity: bool = ...
    use_id_for_hash: bool = ...
    mapper: Any = ...
    aliased_adapter: Any = ...
    selectable: Any = ...
    is_aliased_class: Any = ...
    entity_zero: Any = ...
    path: Any = ...
    def setup_entity(self, ext_info, aliased_adapter): ...
    def set_with_polymorphic(self, query, cls_or_mappers, selectable, polymorphic_on): ...
    @property
    def type(self): ...
    @property
    def entity_zero_or_selectable(self): ...
    def corresponds_to(self, entity): ...
    def adapt_to_selectable(self, query, sel): ...
    def row_processor(self, query, context, result): ...
    def setup_context(self, query, context): ...

class Bundle(InspectionAttr):
    single_entity: bool = ...
    is_clause_element: bool = ...
    is_mapper: bool = ...
    is_aliased_class: bool = ...
    name: str = ...
    exprs: Any = ...
    c: Any = ...
    def __init__(self, name, *exprs, **kw) -> None: ...
    columns: Any = ...
    def __clause_element__(self): ...
    @property
    def clauses(self): ...
    def label(self, name): ...
    def create_row_processor(self, query, procs, labels): ...

class _BundleEntity(_QueryEntity):
    use_id_for_hash: bool = ...
    bundle: Any = ...
    type: Any = ...
    supports_single_entity: Any = ...
    def __init__(self, query, bundle, setup_entities: bool = ...) -> None: ...
    @property
    def entities(self): ...
    @property
    def entity_zero(self): ...
    def corresponds_to(self, entity): ...
    @property
    def entity_zero_or_selectable(self): ...
    def adapt_to_selectable(self, query, sel): ...
    def setup_entity(self, ext_info, aliased_adapter): ...
    def setup_context(self, query, context): ...
    def row_processor(self, query, context, result): ...

class _ColumnEntity(_QueryEntity):
    expr: Any = ...
    namespace: Any = ...
    type: Any = ...
    use_id_for_hash: Any = ...
    column: Any = ...
    froms: Any = ...
    actual_froms: Any = ...
    entity_zero: Any = ...
    entities: Any = ...
    mapper: Any = ...
    def __init__(self, query, column, namespace: Optional[Any] = ...) -> None: ...
    supports_single_entity: bool = ...
    @property
    def entity_zero_or_selectable(self): ...
    def adapt_to_selectable(self, query, sel): ...
    selectable: Any = ...
    def setup_entity(self, ext_info, aliased_adapter): ...
    def corresponds_to(self, entity): ...
    def row_processor(self, query, context, result): ...
    def setup_context(self, query, context): ...

class QueryContext(object):
    statement: Any = ...
    from_clause: Any = ...
    whereclause: Any = ...
    order_by: Any = ...
    multi_row_eager_loaders: bool = ...
    adapter: Any = ...
    froms: Any = ...
    for_update: Any = ...
    query: Any = ...
    session: Any = ...
    autoflush: Any = ...
    populate_existing: Any = ...
    invoke_all_eagers: Any = ...
    version_check: Any = ...
    refresh_state: Any = ...
    primary_columns: Any = ...
    secondary_columns: Any = ...
    eager_order_by: Any = ...
    eager_joins: Any = ...
    create_eager_joins: Any = ...
    propagate_options: Any = ...
    attributes: Any = ...
    def __init__(self, query) -> None: ...

class AliasOption(interfaces.MapperOption):
    alias: Any = ...
    def __init__(self, alias) -> None: ...
    def process_query(self, query): ...
