from sqlalchemy import Enum as SQLEnum

from app.models.enums import HistoryAction, ProposalStatus

proposal_status_db = SQLEnum(
    ProposalStatus,
    name="proposal_status",
    native_enum=False,
    length=32,
    values_callable=lambda x: [e.value for e in x],
)

history_action_db = SQLEnum(
    HistoryAction,
    name="history_action",
    native_enum=False,
    length=32,
    values_callable=lambda x: [e.value for e in x],
)
