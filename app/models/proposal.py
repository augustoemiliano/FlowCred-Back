from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ProposalStatus
from app.models.types import proposal_status_db


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"), index=True)
    bank: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    property_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    financed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[ProposalStatus] = mapped_column(
        proposal_status_db,
        nullable=False,
        index=True,
        default=ProposalStatus.ANALISE_CREDITO,
    )
    responsible_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    next_stage_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    client = relationship("Client", backref="proposals", lazy="joined")
    responsible = relationship("User", foreign_keys=[responsible_user_id], lazy="joined")
    history_entries = relationship(
        "ProposalHistory",
        back_populates="proposal",
        cascade="all, delete-orphan",
    )
    checklist_items = relationship(
        "ProposalChecklistItem",
        back_populates="proposal",
        cascade="all, delete-orphan",
    )
    documents = relationship(
        "Document",
        back_populates="proposal",
        cascade="all, delete-orphan",
    )
