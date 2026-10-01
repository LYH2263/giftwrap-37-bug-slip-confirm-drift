import json
from datetime import datetime, timezone


def insert_run_locked(c, ticket, created_at=None):
    """Write run inside redeem txn.

    票面即真相：库内行钉住签发时冻结的三边、折边与 paper_m2，
    绝不按确认瞬间的现场盒边/折边重算。
    """
    result = {
        "box_id": ticket["box_id"],
        "length": ticket["length"],
        "width": ticket["width"],
        "height": ticket["height"],
        "overlap": ticket["overlap"],
        "box_surface": ticket["box_surface"],
        "paper_m2": ticket["paper_m2"],
        "ribbon": {"wrap_style": ticket["wrap_style"], "ribbon_m": ticket["ribbon_m"]},
        "ticket_code": ticket["code"],
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
