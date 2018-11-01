from typing import Any, Optional, Union, TypeVar, NoReturn, Iterable, List, Dict, Iterator, MutableMapping, Sequence
from sqlalchemy import util
from .visitors import ClauseVisitor as ClauseVisitor
from .schema import Column
from .elements import ColumnElement
from ..util import PopulateDict
from ..engine.base import Engine, Connection
from ..engine.result import ResultProxy
from .. import util

PARSE_AUTOCOMMIT: util.symbol = ...
NO_ARG: util.symbol = ...

_I = TypeVar('_I', bound=Immutable)

class Immutable(object):
    def unique_params(self, *optionaldict: Any, **kwargs: Any): ...
    def params(self, *optionaldict: Any, **kwargs: Any): ...
    def _clone(self: _I) -> _I: ...

class _DialectArgView(MutableMapping[str, Any]):
    def __getitem__(self, key: str) -> Any: ...
    def __setitem__(self, key: str, value: Any) -> None: ...
    def __delitem__(self, key: str) -> None: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Any]: ...

class DialectKWArgs(object):
    @classmethod
    def argument_for(cls, dialect_name: str, argument_name: str, default: Any) -> None: ...
    @property
    def dialect_kwargs(self) -> _DialectArgView: ...
    @property
    def kwargs(self) -> _DialectArgView: ...
    @property
    def dialect_options(self) -> PopulateDict: ...

class Generative(object): ...

_E = TypeVar('_E', bound=Executable)

class Executable(Generative):
    supports_execution: bool = ...
    def execution_options(self: _E, **kw: Any) -> _E: ...
    def execute(self, *multiparams: Any, **params: Any) -> Optional[ResultProxy]: ...
    def scalar(self, *multiparams: Any, **params: Any) -> Any: ...
    @property
    def bind(self) -> Optional[Union[Engine, Connection]]: ...

class SchemaEventTarget(object): ...

class SchemaVisitor(ClauseVisitor):
    __traverse_options__: Any = ...

class ColumnCollection(util.OrderedProperties[ColumnElement[Any]]):
    def __init__(self, *columns: ColumnElement[Any]) -> None: ...
    def __str__(self) -> str: ...
    def replace(self, column: ColumnElement[Any]) -> None: ...
    def add(self, column: ColumnElement[Any]) -> None: ...
    def __delitem__(self, key: str) -> NoReturn: ...
    def __setattr__(self, key: str, object: ColumnElement[Any]) -> NoReturn: ...
    def __setitem__(self, key: str, value: ColumnElement[Any]) -> None: ...
    def clear(self) -> NoReturn: ...
    def remove(self, column: ColumnElement[Any]) -> None: ...
    # signature incompatible with supertype "Properties"
    def update(self, iter: Iterable[ColumnElement[Any]]) -> None: ...  # type: ignore
    def extend(self, iter: Iterable[ColumnElement[Any]]) -> None: ...
    __hash__: None = ...  # type: ignore
    def __eq__(self, other: Any) -> bool: ...
    def __contains__(self, other: Any) -> bool: ...
    def contains_column(self, col: ColumnElement[Any]) -> bool: ...
    def as_immutable(self) -> ImmutableColumnCollection: ...

class ImmutableColumnCollection(util.ImmutableProperties[ColumnElement[Any]], ColumnCollection):
    def __init__(self, data: Dict[str, Any], all_columns: Sequence[ColumnElement[Any]]) -> None: ...

class ColumnSet(util.ordered_column_set[ColumnElement[Any]]):
    def contains_column(self, col: ColumnElement[Any]) -> bool: ...
    def extend(self, cols: Iterable[ColumnElement[Any]]) -> None: ...
    # Return type of "__add__" incompatible with supertype "OrderedSet"
    def __add__(self, other: Iterable[ColumnElement[Any]]) -> List[ColumnElement[Any]]: ...  # type: ignore
    def __eq__(self, other: Any) -> bool: ...
    def __hash__(self) -> int: ...
