from typing import Any, Optional, Dict, Union, Text
from sqlalchemy import log
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.schema import DDLElement, DefaultGenerator
from sqlalchemy.engine.interfaces import Compiled
from .interfaces import Connectable as Connectable, ExceptionContext as ExceptionContext
from .result import ResultProxy

class Transaction(object):
    connection: Any = ...
    is_active: bool = ...
    def __init__(self, connection, parent) -> None: ...
    def close(self): ...
    def rollback(self): ...
    def commit(self): ...
    def __enter__(self): ...
    def __exit__(self, type, value, traceback): ...

class RootTransaction(Transaction):
    def __init__(self, connection) -> None: ...

class NestedTransaction(Transaction):
    def __init__(self, connection, parent) -> None: ...

class TwoPhaseTransaction(Transaction):
    xid: Any = ...
    def __init__(self, connection, xid) -> None: ...
    def prepare(self): ...

class Connection(Connectable):
    schema_for_object: Any = ...
    engine: Any = ...
    dialect: Any = ...
    should_close_with_result: bool = ...
    dispatch: Any = ...
    def __init__(self, engine, connection: Optional[Any] = ..., close_with_result: bool = ...,
                 _branch_from: Optional[Any] = ..., _execution_options: Optional[Any] = ...,
                 _dispatch: Optional[Any] = ..., _has_events: Optional[Any] = ...) -> None: ...
    def __enter__(self): ...
    def __exit__(self, type, value, traceback): ...
    def execution_options(self, **opt): ...
    @property
    def closed(self) -> bool: ...
    @property
    def invalidated(self) -> bool: ...
    @property
    def connection(self): ...
    def get_isolation_level(self) -> str: ...
    @property
    def default_isolation_level(self) -> str: ...
    @property
    def info(self) -> Dict[Any, Any]: ...
    def connect(self): ...
    def contextual_connect(self, **kwargs): ...
    def invalidate(self, exception: Optional[Any] = ...) -> None: ...
    def detach(self) -> None: ...
    def begin(self) -> Transaction: ...
    def begin_nested(self) -> NestedTransaction: ...
    def begin_twophase(self, xid: Optional[Any] = ...) -> TwoPhaseTransaction: ...
    def recover_twophase(self): ...
    def rollback_prepared(self, xid, recover: bool = ...): ...
    def commit_prepared(self, xid, recover: bool = ...): ...
    def in_transaction(self) -> bool: ...
    def close(self) -> None: ...
    def scalar(self, object, *multiparams, **params): ...
    def execute(self, object, *multiparams, **params) -> ResultProxy: ...
    def transaction(self, callable_, *args, **kwargs): ...
    def run_callable(self, callable_, *args, **kwargs): ...

class ExceptionContextImpl(ExceptionContext):
    engine: Any = ...
    connection: Any = ...
    sqlalchemy_exception: Any = ...
    original_exception: Any = ...
    execution_context: Any = ...
    statement: Any = ...
    parameters: Any = ...
    is_disconnect: bool = ...
    invalidate_pool_on_disconnect: bool = ...
    def __init__(self, exception, sqlalchemy_exception, engine, connection, cursor,
                 statement, parameters, context, is_disconnect,
                 invalidate_pool_on_disconnect) -> None: ...

class Engine(Connectable, log.Identified):
    schema_for_object: Any = ...
    pool: Any = ...
    url: Any = ...
    dialect: Any = ...
    logging_name: Any = ...
    echo: Any = ...
    engine: Any = ...
    def __init__(self, pool, dialect, url, logging_name: Optional[Any] = ..., echo: Optional[Any] = ...,
                 proxy: Optional[Any] = ..., execution_options: Optional[Any] = ...) -> None: ...
    def update_execution_options(self, **opt): ...
    def execution_options(self, **opt): ...
    @property
    def name(self): ...
    @property
    def driver(self): ...
    def dispose(self) -> None: ...
    def begin(self, close_with_result: bool = ...): ...
    def transaction(self, callable_, *args, **kwargs): ...
    def run_callable(self, callable_, *args, **kwargs): ...
    def execute(self,
                object: Union[Text, ClauseElement, FunctionElement, DDLElement, DefaultGenerator, Compiled],
                *multiparams: Any,
                **params: Any) -> ResultProxy: ...
    def scalar(self, statement, *multiparams, **params): ...
    def connect(self, **kwargs) -> Connection: ...
    def contextual_connect(self, close_with_result: bool = ..., **kwargs): ...
    def table_names(self, schema: Optional[Any] = ..., connection: Optional[Any] = ...): ...
    def has_table(self, table_name, schema: Optional[Any] = ...): ...
    def raw_connection(self, _connection: Optional[Any] = ...): ...

class OptionEngine(Engine):
    url: Any = ...
    dialect: Any = ...
    logging_name: Any = ...
    echo: Any = ...
    dispatch: Any = ...
    def __init__(self, proxied, execution_options) -> None: ...
    pool: Any = ...
