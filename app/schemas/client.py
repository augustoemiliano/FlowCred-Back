from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _digits_only(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document: str = Field(min_length=1, max_length=18, description="CPF ou CNPJ (com ou sem máscara)")
    phone: str = Field(min_length=8, max_length=30)
    email: EmailStr
    monthly_income: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("document")
    @classmethod
    def normalize_document(cls, v: str) -> str:
        digits = _digits_only(v)
        if len(digits) not in (11, 14):
            raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
        return digits

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, v: str) -> str:
        return v.strip()

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    document: str = Field(min_length=1, max_length=18)
    phone: str = Field(min_length=8, max_length=30)
    email: EmailStr
    monthly_income: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("document")
    @classmethod
    def normalize_document(cls, v: str) -> str:
        digits = _digits_only(v)
        if len(digits) not in (11, 14):
            raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
        return digits

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, v: str) -> str:
        return v.strip()

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    document: str
    phone: str
    email: str
    monthly_income: Decimal | None
    notes: str | None
    created_at: datetime


class ClientListResponse(BaseModel):
    items: list[ClientRead]
    total: int
    page: int
    page_size: int
