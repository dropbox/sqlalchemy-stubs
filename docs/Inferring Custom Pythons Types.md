`sqlalchemy-stubs` is able to infer the python type based on the column definition for SQLAlchemy models.
Thus,

```python
class User(Base):
    id = Column(Integer, primary_key=True)
```

allows `User().id` to have inferred type `int`. It can be useful to have custom Python types to strengthen type-checking guarantees,
especially for fields such as uuids, emails, phone numbers, transaction tokens, and more. To achieve this, do the following:

```python
from sqlalchemy.dialects.postgresql import UUID  # import your desired column type
from typing import NewType
from uuid import uuid4 as gen_uuid

Uuid = NewType('Uuid', str)  # define the custom Python type to use for typechecking


# define a new column field, giving it a type-decorator for your type, and inheriting from the column type. Order is important here.
class PgUuid(UUID): # type: PgUuid(sqltypes.TypeDecorator[Uuid], UUID)
    pass


def uuid4():
    return str(gen_uuid())


# Now define a model using the column.
class User(Base):
    __tablename__ = 'users'
    uuid = Column(PgUuid(), primary_key=True, default=uuid4)
```

With this class, `User().uuid` will now typecheck to `Uuid`.
