from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import JSON, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ParsedDocument(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "parsed_documents"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), index=True, nullable=False
    )
    revision_id: Mapped[str] = mapped_column(
        ForeignKey("document_revisions.id"), index=True, nullable=False
    )
    parsing_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    parser_used: Mapped[str] = mapped_column(String, nullable=False)
    ocr_version: Mapped[str | None] = mapped_column(String, nullable=True)
    pipeline_version: Mapped[str | None] = mapped_column(String, nullable=True)

    input_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    output_hash: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, default="completed", nullable=False)

    pages = relationship(
        "ParsedPage", back_populates="parsed_document", cascade="all, delete-orphan"
    )


class ParsedPage(Base, AuditMixin):
    __tablename__ = "parsed_pages"

    # We use string for id since Base is used which doesn't provide id natively, wait, Base doesn't provide id.
    # We should inherit from AuditMixin to get id!

    parsed_document_id: Mapped[str] = mapped_column(
        ForeignKey("parsed_documents.id"), index=True, nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    text_content: Mapped[str] = mapped_column(String, nullable=False)

    # FTS vector will be populated by PostgreSQL trigger or manually via SQLAlchemy func.to_tsvector
    fts_vector = mapped_column(TSVECTOR, nullable=True)

    # JSON for bbox layout
    layout_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    parsed_document = relationship("ParsedDocument", back_populates="pages")

    __table_args__ = (
        Index("ix_parsed_pages_fts", "fts_vector", postgresql_using="gin"),
    )


class DocumentChunk(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), index=True, nullable=False
    )
    revision_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_revisions.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    page_id: Mapped[str] = mapped_column(
        ForeignKey("parsed_pages.id"), index=True, nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # "page", "block", "paragraph", "line", "word"
    chunk_type: Mapped[str] = mapped_column(String, nullable=False, default="block")

    text_content: Mapped[str] = mapped_column(String, nullable=False)
    watermarked_text: Mapped[str] = mapped_column(String, nullable=False)
    character_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_version: Mapped[str | None] = mapped_column(String, nullable=True)
    provenance_state: Mapped[str] = mapped_column(
        String, nullable=False, default="LOW_PROVENANCE", index=True
    )

    fts_vector = mapped_column(TSVECTOR, nullable=True)

    # [x0, y0, x1, y1]
    bbox: Mapped[dict] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_document_chunks_fts", "fts_vector", postgresql_using="gin"),
    )
