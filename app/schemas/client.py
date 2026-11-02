from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.documents import digits_only, is_valid_cnpj, is_valid_cpf


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
        digits = digits_only(v)
        if len(digits) == 11:
            if not is_valid_cpf(digits):
                raise ValueError("CPF inválido")
        elif len(digits) == 14:
            if not is_valid_cnpj(digits):
                raise ValueError("CNPJ inválido")
        else:
            raise ValueError("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
        return digits

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, v: str) -> str:
        return v.strip()

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome obrigatório")
        return v


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


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
