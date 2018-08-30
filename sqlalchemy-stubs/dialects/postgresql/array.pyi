from typing import Any as AnyType, Optional, TypeVar, Type, Callable, overload
from ...sql import expression
from ...sql.type_api import TypeEngine
from ... import types as sqltypes

_T = TypeVar('_T')

def Any(other: AnyType, arrexpr: AnyType, operator: Callable[..., AnyType] = ...) -> AnyType: ...
def All(other: AnyType, arrexpr: AnyType, operator: Callable[..., AnyType] = ...) -> AnyType: ...

class array(expression.Tuple): ...
class ARRAY(sqltypes.ARRAY[_T]):
    @overload
    def __init__(self, item_type: TypeEngine[_T], as_tuple: bool = ..., dimensions: Optional[AnyType] = ...,
                 zero_indexes: bool = ...) -> None: ...
    @overload
    def __init__(self, item_type: Type[TypeEngine[_T]], as_tuple: bool = ..., dimensions: Optional[AnyType] = ...,
                 zero_indexes: bool = ...) -> None: ...
