import pytest
from fastapi.testclient import TestClient

from app import seed
from app.db import connect
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("app.db.DB_PATH", str(db_file))
    seed.init_db()
    return TestClient(app)


def issue(client, box_id=1, **kw):
    r = client.post("/api/tickets/issue", json={"box_id": box_id, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def run_count(client, box_id=None):
    url = "/api/runs" if box_id is None else f"/api/runs?box_id={box_id}"
    return len(client.get(url).json()["items"])


# —— 试算：只出面积，绝不落库 ——

def test_preview_never_writes_run(client):
    r = client.get("/api/estimate?box_id=1")
    assert r.status_code == 200
    assert r.json()["paper_m2"] == 0.31
    assert run_count(client) == 0


def test_legacy_save_path_is_rejected(client):
    r = client.post("/api/estimate", json={"box_id": 1, "save": True})
    assert r.status_code == 400
    assert run_count(client) == 0


# —— 签发：服务端登记，行数不变 ——

def test_issue_registers_server_side_without_run(client):
    t = issue(client)
    assert t["code"].startswith("T-")
    assert (t["length"], t["width"], t["height"]) == (0.3, 0.2, 0.15)
    assert t["overlap"] == 1.15
    assert t["paper_m2"] == 0.31
    # 服务端可查（不是浏览器本地变量）
    assert client.get(f"/api/tickets/{t['code']}").json()["status"] == "open"
    assert run_count(client) == 0


def test_dirty_box_cannot_be_issued(client):
    r = client.post("/api/tickets/issue", json={"box_id": 3})
    assert r.status_code == 422
    assert run_count(client) == 0


# —— 确认：票面原样写一行并核销 ——

def test_confirm_writes_face_verbatim_and_redeems(client):
    t = issue(client)
    r = client.post("/api/tickets/confirm", json={"code": t["code"]})
    assert r.status_code == 200, r.text
    done = r.json()
    assert done["run_id"] is not None
    for k in ("length", "width", "height", "overlap", "box_surface", "paper_m2"):
        assert done[k] == t[k]
    assert done["paper_m2"] == 0.31

    assert client.get(f"/api/tickets/{t['code']}").json()["status"] == "redeemed"
    rows = client.get("/api/runs").json()["items"]
    assert len(rows) == 1
    assert rows[0]["ticket_code"] == t["code"]
    assert rows[0]["result"]["paper_m2"] == 0.31
    assert rows[0]["result"]["overlap"] == 1.15


def test_missing_ticket_fails_without_row(client):
    r = client.post("/api/tickets/confirm", json={"code": "T-NOPE"})
    assert r.status_code == 404
    assert run_count(client) == 0


def test_double_confirm_conflicts_and_single_row(client):
    t = issue(client)
    assert client.post("/api/tickets/confirm", json={"code": t["code"]}).status_code == 200
    r = client.post("/api/tickets/confirm", json={"code": t["code"]})
    assert r.status_code == 409
    assert run_count(client) == 1


def test_box_edge_changed_after_issue_fails(client):
    t = issue(client)
    c = connect()
    c.execute("UPDATE boxes SET height=0.18 WHERE id=1")
    c.commit()
    c.close()

    r = client.post("/api/tickets/confirm", json={"code": t["code"]})
    assert r.status_code == 409
    assert "高" in r.json()["detail"]
    # 不加行、未核销
    assert run_count(client) == 0
    assert client.get(f"/api/tickets/{t['code']}").json()["status"] == "open"


def test_overlap_changed_after_issue_fails(client):
    t = issue(client)
    c = connect()
    c.execute("UPDATE settings SET value='1.25' WHERE key='overlap'")
    c.commit()
    c.close()

    r = client.post("/api/tickets/confirm", json={"code": t["code"]})
    assert r.status_code == 409
    assert "折边" in r.json()["detail"]
    assert run_count(client) == 0
    assert client.get(f"/api/tickets/{t['code']}").json()["status"] == "open"


def test_face_truth_beats_live_recompute(client):
    """票面快照即真相：即使库里票面 paper_m2 被改写成与三边不符的数，
    确认也照票面写入，绝不按现场三边/折边重算。"""
    t = issue(client)
    c = connect()
    c.execute("UPDATE estimate_tickets SET paper_m2=9.999 WHERE code=?", (t["code"],))
    c.commit()
    c.close()

    r = client.post("/api/tickets/confirm", json={"code": t["code"]})
    assert r.status_code == 200
    assert r.json()["paper_m2"] == 9.999
    row = client.get("/api/runs").json()["items"][0]
    assert row["result"]["paper_m2"] == 9.999


# —— 列表与详情：钉住票面同一组数字 ——

def test_runs_filter_by_box(client):
    t1 = issue(client, box_id=1)
    t2 = issue(client, box_id=2)
    client.post("/api/tickets/confirm", json={"code": t1["code"]})
    client.post("/api/tickets/confirm", json={"code": t2["code"]})

    box1 = client.get("/api/runs?box_id=1").json()["items"]
    box2 = client.get("/api/runs?box_id=2").json()["items"]
    assert len(box1) == 1 and box1[0]["box_id"] == 1
    assert len(box2) == 1 and box2[0]["box_id"] == 2
    assert len(client.get("/api/runs").json()["items"]) == 2


def test_concurrent_double_confirm_yields_single_row(tmp_path, monkeypatch):
    """两个连接同时确认同一条纸条：行锁串行化，只允许一行落库。"""
    import threading
    from fastapi.testclient import TestClient

    monkeypatch.setattr("app.db.DB_PATH", str(tmp_path / "conc.db"))
    seed.init_db()

    t = TestClient(app).post("/api/tickets/issue", json={"box_id": 1}).json()
    statuses = []

    def worker():
        r = TestClient(app).post("/api/tickets/confirm", json={"code": t["code"]})
        statuses.append(r.status_code)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    assert sorted(statuses) == [200, 409]
    rows = TestClient(app).get("/api/runs").json()["items"]
    assert len(rows) == 1
