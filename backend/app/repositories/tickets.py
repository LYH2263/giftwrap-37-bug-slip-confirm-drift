import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.db import connect


def _now():
    return datetime.now(timezone.utc).isoformat()


def create(face: dict) -> tuple[int, str]:
    """签发登记：服务端生成一次性编号并冻结票面快照。"""
    c = connect()
    try:
        for _ in range(8):
            code = "T-" + secrets.token_hex(6).upper()
            try:
                cur = c.execute(
                    """INSERT INTO estimate_tickets(
                           code,box_id,box_name,length,width,height,overlap,
                           box_surface,paper_m2,wrap_style,ribbon_m,status,note,issued_at
                       ) VALUES (?,?,?,?,?,?,?,?,?,?,?,'open',?,?)""",
                    (
                        code,
                        face["box_id"],
                        face["box_name"],
                        face["length"],
                        face["width"],
                        face["height"],
                        face["overlap"],
                        face["box_surface"],
                        face["paper_m2"],
                        face["wrap_style"],
                        face["ribbon_m"],
                        face.get("note", ""),
                        _now(),
                    ),
                )
                c.commit()
                return int(cur.lastrowid), code
            except sqlite3.IntegrityError:
                continue  # code 碰撞，换一个
        raise RuntimeError("无法分配唯一纸条编号")
    finally:
        c.close()


def find_by_code(code: str) -> dict | None:
    c = connect()
    try:
        row = c.execute(
            "SELECT * FROM estimate_tickets WHERE code=?", (code,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        c.close()


@contextmanager
def locked_ticket(code: str):
    """开启 IMMEDIATE 写事务并取出纸条；并发确认在此串行化。

    with 块正常退出即提交，抛异常即回滚；调用方在块内完成校验、写 run、
    标记核销，保证“核销 + 写行”同生共死。
    """
    c = connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        row = c.execute(
            "SELECT * FROM estimate_tickets WHERE code=?", (code,)
        ).fetchone()
        try:
            yield c, (dict(row) if row else None)
        except Exception:
            c.rollback()
            raise
        else:
            c.commit()
    finally:
        c.close()


def mark_redeemed(c, ticket_id: int, run_id: int) -> None:
    """原子核销：仅当纸条仍处于 open 才置位，否则整事务回滚。"""
    cur = c.execute(
        "UPDATE estimate_tickets SET status='redeemed',run_id=?,redeemed_at=? WHERE id=? AND status='open'",
        (run_id, _now(), ticket_id),
    )
    if cur.rowcount != 1:
        raise RuntimeError("纸条已被核销，拒绝重复确认")
