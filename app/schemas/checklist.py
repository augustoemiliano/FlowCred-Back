from pydantic import BaseModel, ConfigDict, Field


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proposal_id: int
    title: str
    is_done: bool
    sort_order: int


class ChecklistItemPatch(BaseModel):
    is_done: bool = Field(description="Marcar ou desmarcar item")
