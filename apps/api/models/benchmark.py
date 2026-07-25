from apps.api.core.models import AuditMixin, Base
from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class BenchmarkDataset(Base, AuditMixin):
    __tablename__ = "legal_benchmark_datasets"
    
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False) # e.g., 'LEGAL', 'MEDICAL'
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class BenchmarkItem(Base, AuditMixin):
    __tablename__ = "legal_benchmark_items"
    
    dataset_id: Mapped[str] = mapped_column(ForeignKey("legal_benchmark_datasets.id"), index=True, nullable=False)
    split_type: Mapped[str] = mapped_column(String, index=True, nullable=False) # 'train', 'dev', 'holdout'
    
    # Task definition (e.g. query, question, target extraction context)
    task_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Flags for leakage detection
    temporal_version: Mapped[str | None] = mapped_column(String, nullable=True)
    requires_anonymization: Mapped[bool] = mapped_column(Boolean, default=True)
    
    dataset = relationship("BenchmarkDataset")

class GoldAnnotation(Base, AuditMixin):
    __tablename__ = "legal_gold_annotations"
    
    item_id: Mapped[str] = mapped_column(ForeignKey("legal_benchmark_items.id"), index=True, nullable=False)
    
    # Adjudication schema (e.g. true answer, extracted entity, citation gold set)
    expected_output: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # E.g. which lawyer adjudicated this gold set
    adjudicator_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    item = relationship("BenchmarkItem")
