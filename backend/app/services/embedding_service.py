"""Embedding service for vectorizing activities using Agno framework."""

from uuid import UUID

from agno.knowledge.embedder.ollama import OllamaEmbedder
from loguru import logger
from sqlmodel import Session, select

from app.core.config import settings
from app.models.activity import Activity
from app.models.activity_embedding import ActivityEmbedding
from app.services.chunkers.time_block_chunker import TimeBlockChunker


class EmbeddingService:
    """Service for embedding activities into vectors.

    Uses Agno framework to support multiple embedding providers.
    """

    def __init__(self):
        """Initialize embedding service with configured embedder."""
        self.chunker = TimeBlockChunker()

        # Create embedder based on configuration
        if settings.embedder.provider == "ollama":
            self.embedder = OllamaEmbedder(
                id=settings.embedder.model_name,
                dimensions=settings.embedder.dimensions,
                host=settings.embedder.base_url,
            )
        else:
            raise ValueError(
                f"Unsupported embedder provider: {settings.embedder.provider}"
            )

        logger.info(
            "Initialized EmbeddingService with {provider} ({model})",
            provider=settings.embedder.provider,
            model=settings.embedder.model_name,
        )

    def embed_activity(
        self,
        activity: Activity,
        user_id: UUID,
        session: Session,
        force_regenerate: bool = False,
    ) -> list[ActivityEmbedding]:
        """Embed a single activity into vector chunks.

        Args:
            activity: Activity to embed
            user_id: User ID for data isolation
            session: Database session
            force_regenerate: If True, delete existing embeddings and regenerate

        Returns:
            List of ActivityEmbedding records created (empty if skipped)
        """
        # Check if embeddings already exist
        existing_embeddings = session.exec(
            select(ActivityEmbedding).where(
                ActivityEmbedding.activity_id == activity.id
            )
        ).all()

        # If embeddings exist and not forcing regeneration, skip
        if existing_embeddings and not force_regenerate:
            logger.info(
                f"Activity {activity.id} already has {len(existing_embeddings)} embeddings, skipping"
            )
            return []

        # If forcing regeneration, delete old embeddings
        if existing_embeddings and force_regenerate:
            deleted_count = len(existing_embeddings)
            for embedding in existing_embeddings:
                session.delete(embedding)
            session.commit()
            logger.info(
                f"Deleted {deleted_count} old embeddings for updated activity {activity.id}"
            )

        # Extract detailed_summary for chunking
        detailed_summary = activity.extra_data.get("detailed_summary", "")

        # Prepare metadata for chunks
        chunk_metadata = {
            "day": activity.extra_data.get("day"),
            "title": activity.title,
            "category": activity.extra_data.get("category"),
            "subcategory": activity.extra_data.get("subcategory"),
        }

        # Chunk the text
        if detailed_summary:
            chunks = self.chunker.chunk(detailed_summary, metadata=chunk_metadata)
        else:
            # Fallback: use title and content as single chunk
            from app.services.chunkers.base import Chunk

            chunks = [
                Chunk(
                    text=f"{activity.title}\n{activity.content or ''}",
                    index=0,
                    metadata=chunk_metadata,
                )
            ]

        if not chunks:
            logger.warning(f"No chunks generated for activity {activity.id}")
            return []

        # Prepare texts for batch embedding
        chunk_texts = [chunk.text for chunk in chunks]

        # Get embeddings from Agno
        try:
            # Agno embedders use the embed() method for single text
            embeddings = []
            for text in chunk_texts:
                embedding = self.embedder.get_embedding(text)
                embeddings.append(embedding)
        except Exception as e:
            logger.exception(f"Failed to embed activity {activity.id}: {e=}")
            raise

        # Create ActivityEmbedding records
        embedding_records = []
        for chunk, embedding_vector in zip(chunks, embeddings, strict=True):
            if not embedding_vector:
                logger.error(f"{chunk=}, {embedding_vector=}")
                continue
            record = ActivityEmbedding(
                activity_id=activity.id,
                user_id=user_id,
                embedding=embedding_vector,
                chunk_text=chunk.text,
                chunk_index=chunk.index,
                chunk_metadata=chunk.metadata or {},
                embedder_model=settings.embedder.model_name,
                embedder_provider=settings.embedder.provider,
            )
            session.add(record)
            embedding_records.append(record)

        logger.info(
            f"Created {len(embedding_records)} embeddings for activity {activity.id}"
        )

        return embedding_records

    def embed_activities_batch(
        self,
        activities: list[Activity],
        user_id: UUID,
        session: Session,
        batch_size: int | None = None,
        force_regenerate_ids: set[int] | None = None,
    ) -> int:
        """Embed multiple activities in batches.

        Args:
            activities: List of activities to embed
            user_id: User ID for data isolation
            session: Database session
            batch_size: Batch size for committing (default: 10)
            force_regenerate_ids: Set of activity IDs that should be force regenerated

        Returns:
            Number of activities successfully embedded
        """
        batch_size = batch_size or 10
        force_regenerate_ids = force_regenerate_ids or set()
        success_count = 0

        for i, activity in enumerate(activities):
            try:
                force_regenerate = activity.id in force_regenerate_ids
                self.embed_activity(
                    activity, user_id, session, force_regenerate=force_regenerate
                )
                success_count += 1

                # Commit in batches
                if (i + 1) % batch_size == 0:
                    session.commit()
                    logger.info(
                        f"Committed batch {(i + 1) // batch_size} ({i + 1} activities)"
                    )
            except Exception as e:
                logger.exception(
                    f"Failed to embed activity {activity.id}: {e=}",
                )
                session.rollback()
                continue

        # Commit remaining
        if success_count % batch_size != 0:
            session.commit()

        logger.info(
            f"Batch embedding completed: {success_count}/{len(activities)} activities embedded"
        )

        return success_count
