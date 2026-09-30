"""算纸台：只出面积预览；落库改走「签发纸条 → 凭条确认」两步。

- run_estimate 永远不落库（save 参数仅为兼容旧调用，被忽略并禁用）。
- issue / confirm 分别由 modules.ticket / modules.paper_run 负责。
"""
from fastapi import HTTPException

from app.engines.wrap_math import paper_area, ribbon_estimate
from app.modules import paper_run, ticket
from app.repositories import boxes, settings_repo


def run_estimate(box_id: int, overlap: float | None, wrap_style: str, save: bool = False):
    if save:
        # 不允许再直接写用纸档：必须先签发一次性纸条、凭条确认
        raise HTTPException(400, "直写用纸档已停用，请先签发估纸条再确认")

    box = boxes.get_box(box_id)
    if not box:
        raise HTTPException(404, "礼盒不存在")
    if box.get("data_quality") == "dirty":
        raise HTTPException(422, "脏数据盒不可试算")

    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()
    calc = paper_area(box["length"], box["width"], box["height"], ov)
    ribbon = ribbon_estimate(box["length"], box["width"], box["height"], wrap_style)
    return {"box": box, "run_id": None, **calc, "ribbon": ribbon}


def issue(box_id: int, overlap: float | None, wrap_style: str, note: str = ""):
    return ticket.issue_ticket(box_id, overlap, wrap_style, note)


def confirm(code: str):
    return paper_run.confirm_ticket(code)
