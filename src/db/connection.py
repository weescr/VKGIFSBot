from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.base import container

db_session: ContextVar[AsyncSession | None] = ContextVar("db_session", default=None)


class Transaction:
    async def __aenter__(self):
        session_maker = container.resolve(sessionmaker)
        self.session: AsyncSession = session_maker()
        self.token = db_session.set(self.session)

    async def __aexit__(self, exception_type, exception, traceback):
        if exception:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
        db_session.reset(self.token)