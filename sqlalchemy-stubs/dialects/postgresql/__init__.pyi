from typing import Any as _AnyType

from .array import array as array, ARRAY as ARRAY, Any as Any, All as All

def __getattr__(attr: str) -> _AnyType: ...
