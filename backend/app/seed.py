from app.db import connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS boxes(id INTEGER PRIMARY KEY,name TEXT,length REAL,width REAL,height REAL,data_quality TEXT,note TEXT);
CREATE TABLE IF NOT EXISTS papers(id INTEGER PRIMARY KEY,name TEXT,roll_width REAL,data_quality TEXT,note TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE IF NOT EXISTS calc_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,box_id INT,overlap REAL,result_json TEXT,note TEXT,created_at TEXT,ticket_code TEXT);
CREATE TABLE IF NOT EXISTS estimate_tickets(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  box_id INTEGER NOT NULL,
  box_name TEXT,
  length REAL NOT NULL,
  width REAL NOT NULL,
  height REAL NOT NULL,
  overlap REAL NOT NULL,
  box_surface REAL NOT NULL,
  paper_m2 REAL NOT NULL,
  wrap_style TEXT NOT NULL,
  ribbon_m REAL,
  status TEXT NOT NULL DEFAULT 'open',
  run_id INTEGER,
  note TEXT DEFAULT '',
  issued_at TEXT NOT NULL,
  redeemed_at TEXT
);
"""

def init_db():
    c = connect()
    c.executescript(SCHEMA)
    # 既有库迁移：calc_runs 关联一次性纸条编号
    cols = [r["name"] for r in c.execute("PRAGMA table_info(calc_runs)").fetchall()]
    if "ticket_code" not in cols:
        c.execute("ALTER TABLE calc_runs ADD COLUMN ticket_code TEXT")
    if c.execute("SELECT COUNT(*) c FROM boxes").fetchone()["c"] == 0:
        c.executemany("INSERT INTO boxes(name,length,width,height,data_quality,note) VALUES (?,?,?,?,?,?)",[
            ("书型盒",0.30,0.20,0.15,"clean",""),
            ("方形礼盒",0.25,0.25,0.10,"clean",""),
            ("脏数据-负高",0.2,0.2,-0.1,"dirty","高度负"),
        ])
        c.executemany("INSERT INTO papers(name,roll_width,data_quality,note) VALUES (?,?,?,?)",[
            ("哑光纸1.0m",1.0,"clean",""),
            ("牛皮纸0.7m",0.7,"clean",""),
        ])
        c.execute("INSERT INTO settings(key,value) VALUES ('overlap','1.15')")
    c.commit()
    c.close()
