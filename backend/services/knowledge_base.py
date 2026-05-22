"""FAISS vector knowledge base for packages, food, and attractions."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from sqlalchemy import select

from database import AsyncSessionLocal
from models.attraction import Attraction
from models.food_item import FoodItem
from models.package import Package
from services.llm_provider import llm_service

logger = logging.getLogger(__name__)

DOMAINS = ("packages", "food", "attractions")
FAISS_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss"


class KnowledgeBase:
    """Manages per-domain FAISS indexes for semantic retrieval."""

    def __init__(self) -> None:
        self._stores: dict[str, FAISS] = {}
        FAISS_DIR.mkdir(parents=True, exist_ok=True)

    def _index_path(self, domain: str) -> Path:
        return FAISS_DIR / domain

    def _has_index(self, domain: str) -> bool:
        path = self._index_path(domain)
        return path.is_dir() and (path / "index.faiss").exists()

    async def add_documents(
        self,
        domain: str,
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add documents to a domain index (creates or extends the store)."""
        if domain not in DOMAINS:
            raise ValueError(f"Unknown domain: {domain}. Must be one of {DOMAINS}")
        if len(documents) != len(metadatas):
            raise ValueError("documents and metadatas must have the same length")

        docs = [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(documents, metadatas, strict=True)
        ]

        loop = asyncio.get_event_loop()

        def _add() -> FAISS:
            if domain in self._stores:
                self._stores[domain].add_documents(docs)
                return self._stores[domain]
            return FAISS.from_documents(docs, llm_service.embeddings)

        self._stores[domain] = await loop.run_in_executor(None, _add)
        await self._save_domain(domain)
        logger.info("Added %d documents to '%s' index", len(docs), domain)

    async def similarity_search(self, domain: str, query: str, k: int = 5) -> list[dict]:
        """Search a domain index and return content + metadata dicts."""
        if domain not in self._stores:
            if self._has_index(domain):
                await self._load_domain(domain)
            else:
                return []

        store = self._stores[domain]
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, lambda: store.similarity_search_with_score(query, k=k)
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    async def load_all(self) -> None:
        """Load all FAISS indexes from disk if they exist."""
        loaded = []
        for domain in DOMAINS:
            if not self._has_index(domain):
                continue
            try:
                await self._load_domain(domain)
                loaded.append(domain)
            except Exception as exc:
                logger.warning(
                    "Could not load FAISS index '%s' (rebuild with seed scripts if needed): %s",
                    domain,
                    exc,
                )
        if loaded:
            logger.info("Loaded FAISS indexes: %s", ", ".join(loaded))
        else:
            logger.info("No FAISS indexes loaded — run build_from_db() after seeding data")

    async def build_from_db(self) -> None:
        """Rebuild all FAISS indexes from PostgreSQL data."""
        async with AsyncSessionLocal() as db:
            packages = (await db.execute(select(Package).where(Package.is_active.is_(True)))).scalars().all()
            food_items = (
                await db.execute(select(FoodItem).where(FoodItem.is_available.is_(True)))
            ).scalars().all()
            attractions = (
                await db.execute(select(Attraction).where(Attraction.is_active.is_(True)))
            ).scalars().all()

        self._stores.clear()

        if packages:
            await self.add_documents(
                "packages",
                [_package_document(p) for p in packages],
                [_package_metadata(p) for p in packages],
            )
        if food_items:
            await self.add_documents(
                "food",
                [_food_document(f) for f in food_items],
                [_food_metadata(f) for f in food_items],
            )
        if attractions:
            await self.add_documents(
                "attractions",
                [_attraction_document(a) for a in attractions],
                [_attraction_metadata(a) for a in attractions],
            )

        logger.info(
            "Built FAISS indexes — packages=%d food=%d attractions=%d",
            len(packages),
            len(food_items),
            len(attractions),
        )

    async def _save_domain(self, domain: str) -> None:
        """Persist a domain index to disk."""
        store = self._stores.get(domain)
        if store is None:
            return
        path = str(self._index_path(domain))
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: store.save_local(path))
        logger.debug("Saved FAISS index for '%s' to %s", domain, path)

    async def _load_domain(self, domain: str) -> None:
        """Load a domain index from disk."""
        path = str(self._index_path(domain))
        loop = asyncio.get_event_loop()

        def _load() -> FAISS:
            return FAISS.load_local(
                path,
                llm_service.embeddings,
                allow_dangerous_deserialization=True,
            )

        self._stores[domain] = await loop.run_in_executor(None, _load)
        logger.debug("Loaded FAISS index for '%s' from %s", domain, path)


def _package_document(pkg: Package) -> str:
    meta = pkg.package_meta or {}
    meta_line = ""
    if meta:
        parts = []
        if meta.get("for_whom"):
            parts.append(f"For: {meta['for_whom']}")
        if meta.get("duration"):
            parts.append(f"Duration: {meta['duration']}")
        if meta.get("special_highlight"):
            parts.append(f"Highlight: {meta['special_highlight']}")
        meta_line = " ".join(parts)
    return (
        f"Package: {pkg.name}. Tier: {pkg.tier.value}. "
        f"Price: ${pkg.price_per_night_usd}/night. "
        f"Description: {pkg.description or ''}. "
        f"{meta_line} "
        f"Inclusions: {', '.join(pkg.inclusions or [])}. "
        f"Exclusions: {', '.join(pkg.exclusions or [])}. "
        f"Travel styles: {', '.join(pkg.travel_styles or [])}. "
        f"Group types: {', '.join(pkg.group_types or [])}. "
        f"Min nights: {pkg.min_nights}. Max guests: {pkg.max_guests}. "
        f"Seasonal note: {pkg.seasonal_note or 'N/A'}."
    )


def _package_metadata(pkg: Package) -> dict[str, Any]:
    return {
        "id": str(pkg.id),
        "name": pkg.name,
        "tier": pkg.tier.value,
        "domain": "packages",
    }


def _food_document(item: FoodItem) -> str:
    return (
        f"Dish: {item.name}. Meal: {item.meal_type.value}. "
        f"Spice: {item.spice_level.value}. "
        f"Description: {item.description_plain_english or ''}. "
        f"Ingredients: {', '.join(item.ingredients or [])}. "
        f"Dietary tags: {', '.join(item.dietary_tags or [])}. "
        f"Allergens: {', '.join(item.allergens or [])}. "
        f"Cultural note: {item.cultural_note or ''}."
    )


def _food_metadata(item: FoodItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "name": item.name,
        "meal_type": item.meal_type.value,
        "domain": "food",
    }


def _attraction_document(att: Attraction) -> str:
    return (
        f"Attraction: {att.name}. Category: {att.category.value}. "
        f"Description: {att.description or ''}. "
        f"Distance from cabana: {att.distance_km_from_cabana} km. "
        f"Duration: {att.estimated_duration_hours} hours. "
        f"Entry fee: ${att.entry_fee_usd or 0}. "
        f"Fitness level: {att.fitness_level_required.value}. "
        f"Suitable for: {', '.join(att.suitable_for or [])}. "
        f"Tips: {att.tips or ''}."
    )


def _attraction_metadata(att: Attraction) -> dict[str, Any]:
    return {
        "id": str(att.id),
        "name": att.name,
        "category": att.category.value,
        "domain": "attractions",
    }


knowledge_base = KnowledgeBase()
