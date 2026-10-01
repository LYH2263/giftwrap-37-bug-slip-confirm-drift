"""写用纸档：凭未核销纸条确认，票面原样写一行用纸档并核销。"""
from fastapi import HTTPException

from app.modules import redeem
from app.repositories import boxes, history, settings_repo, tickets as ticket_repo


def confirm_ticket(code: str) -> dict:
    with ticket_repo.locked_ticket(code) as (c, ticket):
        if ticket is None:
            raise HTTPException(404, "纸条不存在或已失效")

        redeem.require_open(ticket)

        current_box = boxes.get_box(ticket["box_id"])
        current_ov = settings_repo.get_overlap()
        redeem.require_face_unchanged(ticket, current_box, current_ov)

        # 票面原样写一行，随后核销；两者同处 IMMEDIATE 事务，同生共死
        run_id = history.insert_run_locked(c, ticket)
        ticket_repo.mark_redeemed(c, ticket["id"], run_id)

    return {
        "run_id": run_id,
        "code": ticket["code"],
        "box_id": ticket["box_id"],
        "box_name": ticket["box_name"],
        "length": ticket["length"],
        "width": ticket["width"],
        "height": ticket["height"],
        "overlap": ticket["overlap"],
        "box_surface": ticket["box_surface"],
        "paper_m2": ticket["paper_m2"],
    }
