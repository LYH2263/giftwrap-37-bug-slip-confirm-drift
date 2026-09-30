from pydantic import BaseModel

class EstimateRequest(BaseModel):
    box_id: int
    overlap: float | None = None
    wrap_style: str = "cross"
    # 旧版直写用纸档入口保留字段以显式拒绝；落库须走签发+确认
    save: bool = False

class TicketIssueRequest(BaseModel):
    box_id: int
    overlap: float | None = None
    wrap_style: str = "cross"
    note: str = ""

class TicketConfirmRequest(BaseModel):
    code: str
