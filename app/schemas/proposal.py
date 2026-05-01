from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProposalStatus


class ClientMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    document: str


class UserMinimal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class ProposalCreate(BaseModel):
    client_id: int = Field(ge=1)
    bank: str = Field(min_length=1, max_length=255)
    property_value: Decimal = Field(gt=0)
    financed_amount: Decimal = Field(gt=0)
    status: ProposalStatus = ProposalStatus.ANALISE_CREDITO
    responsible_user_id: int = Field(ge=1)
    next_stage_date: date | None = None
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator("bank")
    @classmethod
    def strip_bank(cls, v: str) -> str:
        return v.strip()


class ProposalUpdate(BaseModel):
    client_id: int = Field(ge=1)
    bank: str = Field(min_length=1, max_length=255)
    property_value: Decimal = Field(gt=0)
    financed_amount: Decimal = Field(gt=0)
    responsible_user_id: int = Field(ge=1)
    next_stage_date: date | None = None
    notes: str | None = Field(default=None, max_length=20000)
    observation: str | None = Field(default=None, max_length=2000, description="Observação para o histórico")

    @field_validator("bank")
    @classmethod
    def strip_bank(cls, v: str) -> str:
        return v.strip()


class ProposalStatusPatch(BaseModel):
    status: ProposalStatus
    note: str | None = Field(default=None, max_length=2000)


class ProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    client_id: int
    bank: str
    property_value: Decimal
    financed_amount: Decimal
    status: ProposalStatus
    responsible_user_id: int
    next_stage_date: date | None
    notes: str | None
    created_at: datetime


class ProposalDetailRead(ProposalRead):
    client: ClientMinimal
    responsible: UserMinimal


class ProposalListResponse(BaseModel):
    items: list[ProposalRead]
    total: int
    page: int
    page_size: int


class ProposalHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    proposal_id: int
    user_id: int
    user_username: str | None = None
    action: str
    old_status: ProposalStatus | None
    new_status: ProposalStatus | None
    note: str | None
    created_at: datetime
