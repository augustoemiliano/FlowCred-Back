from decimal import Decimal

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_proposals: int
    proposals_em_analise: int = Field(description="Status ANALISE_CREDITO")
    proposals_juridico: int
    proposals_finalizadas: int
    total_financed_amount: Decimal
    proposals_by_status: dict[str, int]
    proposals_by_bank: dict[str, int]
