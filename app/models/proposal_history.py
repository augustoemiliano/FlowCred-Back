from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import HistoryAction, ProposalStatus
from app.models.types import history_action_db, proposal_status_db


class ProposalHistory(Base):
    __tablename__ = "proposal_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    action: Mapped[HistoryAction] = mapped_column(history_action_db, nullable=False)
    old_status: Mapped[ProposalStatus | None] = mapped_column(proposal_status_db, nullable=True)
    new_status: Mapped[ProposalStatus | None] = mapped_column(proposal_status_db, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    proposal = relationship("Proposal", back_populates="history_entries")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
