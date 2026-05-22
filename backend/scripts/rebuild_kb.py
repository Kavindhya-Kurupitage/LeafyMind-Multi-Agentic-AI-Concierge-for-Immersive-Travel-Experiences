"""Rebuild FAISS knowledge-base indexes from the database."""

import asyncio

from database import init_db
from services.knowledge_base import knowledge_base


async def main() -> None:
    await init_db()
    await knowledge_base.build_from_db()
    print("FAISS knowledge base rebuilt from database.")


if __name__ == "__main__":
    asyncio.run(main())
