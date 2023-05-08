import sys

from typing import Any, List, Mapping, Union, AbstractSet, Tuple
from ..sql.schema import Column

if sys.version_info >= (3, 0):
    _RowItems = AbstractSet[Tuple[str, Any]]
else:
    _RowItems = List[Tuple[str, Any]]

class BaseRow(Mapping[str, Any]):
    def __init__(self, parent, row, processors, keymap, data) -> None: ...
    def __reduce__(self): ...
    def values(self): ...
    def __iter__(self): ...
    def __len__(self) -> int: ...
    def __getitem__(self, key: Union[str, int, Column]) -> Any: ...
    def __getattr__(self, name): ...

class Row(BaseRow):
    def __contains__(self, key): ...
    __hash__: Any = ...
    def __lt__(self, other): ...
    def __le__(self, other): ...
    def __ge__(self, other): ...
    def __gt__(self, other): ...
    def __eq__(self, other): ...
    def __ne__(self, other): ...
    def has_key(self, key): ...
    def items(self) -> _RowItems: ...
    def keys(self): ...
    def iterkeys(self): ...
    def itervalues(self): ...

