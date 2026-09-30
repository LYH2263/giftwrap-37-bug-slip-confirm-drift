"""纸条签发模块：试算后签发一次性估纸条，冻结票面快照并服务端登记。

签发本身不写用纸档（calc_runs 行数不变）；编号由服务端生成，
前端无法靠本地变量冒充。
"""
from fastapi import HTTPException

from app.engines.wrap_math import paper_area, ribbon_estimate
from app.repositories import boxes, settings_repo, tickets as ticket_repo


def issue_ticket(box_id: int, overlap: float | None, wrap_style: str, note: str = "") -> dict:
    box = boxes.get_box(box_id)
    if not box:
        raise HTTPException(404, "礼盒不存在")
    if box.get("data_quality") == "dirty":
        raise HTTPException(422, "脏数据盒不可签发")

    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()
    calc = paper_area(box["length"], box["width"], box["height"], ov)
    ribbon = ribbon_estimate(box["length"], box["width"], box["height"], wrap_style)

    face = {
        "box_id": box_id,
        "box_name": box["name"],
        "length": float(box["length"]),
        "width": float(box["width"]),
        "height": float(box["height"]),
        "overlap": calc["overlap"],
        "box_surface": calc["box_surface"],
        "paper_m2": calc["paper_m2"],
        "wrap_style": wrap_style,
        "ribbon_m": ribbon["ribbon_m"],
        "note": note or "",
    }
    _, code = ticket_repo.create(face)
    return {"code": code, "box": box, **face}
