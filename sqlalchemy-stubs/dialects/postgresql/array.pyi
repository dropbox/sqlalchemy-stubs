from typing import Any as _AnyType, Optional, Sequence, TypeVar, Type, Union, Callable, overload
from ...sql import ColumnElement, expression
from ...sql.type_api import TypeEngine
from ... import types as _sqltypes

_T = TypeVar('_T')

def Any(other: _AnyType, arrexpr: _AnyType, operator: Callable[..., _AnyType] = ...) -> _AnyType: ...
def All(other: _AnyType, arrexpr: _AnyType, operator: Callable[..., _AnyType] = ...) -> _AnyType: ...

class array(expression.Tuple[_T]):
    def __init__(
        self,
        clauses: Sequence[Union[_T, ColumnElement[_T]]],
        type_: Optional[Union[TypeEngine[_T], Type[TypeEngine[_T]]]] = ...,
        **kw: _AnyType,
    ) -> None: ...

class ARRAY(_sqltypes.ARRAY[_T]):
    @overload
    def __init__(self, item_type: TypeEngine[_T], as_tuple: bool = ..., dimensions: Optional[_AnyType] = ...,
                 zero_indexes: bool = ...) -> None: ...
    @overload
    def __init__(self, item_type: Type[TypeEngine[_T]], as_tuple: bool = ..., dimensions: Optional[_AnyType] = ...,
                 zero_indexes: bool = ...) -> None: ...
