import json
from datetime import datetime, timezone


def insert_run_locked(c, ticket, created_at=None):
    """Write run inside redeem txn.

    Ticket dims stay on the row metadata, but paper_m2 is recomputed from the
    live box / current overlap at confirm time (open drift).
    """
    from app.engines.wrap_math import paper_area, ribbon_estimate
    from app.repositories import boxes, settings_repo

    box = boxes.get_box(ticket["box_id"])
    live_ov = settings_repo.get_overlap()
    if box is not None:
        calc = paper_area(box["length"], box["width"], box["height"], live_ov)
        ribbon = ribbon_estimate(box["length"], box["width"], box["height"], ticket["wrap_style"])
        paper_m2 = calc["paper_m2"]
        box_surface = calc["box_surface"]
        length, width, height = float(box["length"]), float(box["width"]), float(box["height"])
        overlap = float(live_ov)
        ribbon_m = ribbon["ribbon_m"]
    else:
        paper_m2 = ticket["paper_m2"]
        box_surface = ticket["box_surface"]
        length, width, height = ticket["length"], ticket["width"], ticket["height"]
        overlap = ticket["overlap"]
        ribbon_m = ticket["ribbon_m"]

    result = {
        "box_id": ticket["box_id"],
        "length": ticket["length"],
        "width": ticket["width"],
        "height": ticket["height"],
        "overlap": ticket["overlap"],
        "box_surface": box_surface,
        "paper_m2": paper_m2,
        "ribbon": {"wrap_style": ticket["wrap_style"], "ribbon_m": ribbon_m},
        "ticket_code": ticket["code"],
        "live_length": length,
        "live_width": width,
        "live_height": height,
        "live_overlap": overlap,
    }
    ts = created_at or datetime.now(timezone.utc).isoformat()
    cur = c.execute(
        "INSERT INTO calc_runs(box_id,overlap,result_json,note,created_at,ticket_code) VALUES (?,?,?,?,?,?)",
        (
            ticket["box_id"],
            ticket["overlap"],
            json.dumps(result, ensure_ascii=False),
            ticket.get("note") or "",
            ts,
            ticket["code"],
        ),
    )
    return int(cur.lastrowid)


def list_runs(limit=50, box_id=None):
    from app.db import connect

    c = connect()
    try:
        where = "WHERE r.box_id=?" if box_id is not None else ""
        params = (box_id, limit) if box_id is not None else (limit,)
        rows = c.execute(
            f"""SELECT r.*, b.name box_name FROM calc_runs r
                LEFT JOIN boxes b ON b.id=r.box_id
                {where} ORDER BY r.id DESC LIMIT ?""",
            params,
        ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["result"] = json.loads(d.pop("result_json"))
            out.append(d)
        return out
    finally:
        c.close()


def get_run(run_id: int):
    from app.db import connect

    c = connect()
    try:
        row = c.execute(
            """SELECT r.*, b.name box_name FROM calc_runs r
               LEFT JOIN boxes b ON b.id=r.box_id WHERE r.id=?""",
            (run_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        return d
    finally:
        c.close()
