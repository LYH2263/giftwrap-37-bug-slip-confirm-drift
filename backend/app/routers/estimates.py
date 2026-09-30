from fastapi import APIRouter, Query
from app.repositories import tickets as ticket_repo
from app.schemas.estimate import EstimateRequest, TicketConfirmRequest, TicketIssueRequest
from app.services import estimate_service
from fastapi import HTTPException

router = APIRouter()

@router.get("/estimate")
def get_est(box_id: int = Query(...), overlap: float | None = None, wrap_style: str = "cross"):
    # 仅试算出面积，不落库；写用纸档必须走 /tickets/issue + /tickets/confirm
    return estimate_service.run_estimate(box_id, overlap, wrap_style)

@router.post("/estimate")
def post_est(body: EstimateRequest):
    return estimate_service.run_estimate(body.box_id, body.overlap, body.wrap_style, body.save)

@router.post("/tickets/issue")
def issue_ticket(body: TicketIssueRequest):
    """签发一次性估纸条：登记票面快照（盒 id、三边、折边、paper_m2），不写用纸档。"""
    return estimate_service.issue(body.box_id, body.overlap, body.wrap_style, body.note)

@router.post("/tickets/confirm")
def confirm_ticket(body: TicketConfirmRequest):
    """凭未核销纸条确认：票面原样写一行用纸档并核销；缺条/已核销/票面已变均失败。"""
    return estimate_service.confirm(body.code)

@router.get("/tickets/{code}")
def get_ticket(code: str):
    t = ticket_repo.find_by_code(code)
    if not t:
        raise HTTPException(404, "纸条不存在")
    return t
