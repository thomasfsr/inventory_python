import uuid
from datetime import datetime
from sqlalchemy.orm import registry, mapped_column, Mapped, relationship
from sqlalchemy import (ForeignKey, func, String, BigInteger, 
                        DateTime, Numeric, Boolean)
from sqlalchemy.dialects.postgresql import UUID

table_registry = registry()

@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        init=False,
        primary_key=True,
        insert_default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        init=False, 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        init=False, 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # relationship
    inventory_items: Mapped[list['InventoryItem']] = relationship(
        init=False,
        back_populates='user',
        cascade='all, delete-orphan'
    )

    meta_logs: Mapped[list['MetaLog']] = relationship(
    init=False,
    back_populates='user',
    lazy='dynamic' 
)

@table_registry.mapped_as_dataclass
class MetaLog:
    __tablename__ = 'meta_logs'

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'),nullable=False, index=True)
    n_tokens: Mapped[int] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        init=False, 
        server_default=func.now(), 
        nullable=False
    )
    # relationship
    user: Mapped['User'] = relationship(
        init=False,
        back_populates='meta_logs'
    )


@table_registry.mapped_as_dataclass
class InventoryItem:
    __tablename__ = 'inventory_items'

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('users.id'),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[float] = mapped_column(Numeric(10,2))
    unit: Mapped[str] = mapped_column(String(10))
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        init=False, 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        init=False, 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    user: Mapped[User] = relationship(init=False, back_populates="inventory_items")


if __name__ == '__main__':
    from dotenv import load_dotenv
    import os
    load_dotenv()
    from sqlalchemy import create_engine
    url = os.getenv("DATABASE_URL_PSY")
    engine = create_engine(url)
    table_registry.metadata.create_all(engine)
    print('tables created.')