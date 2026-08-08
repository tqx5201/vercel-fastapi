from fastapi import FastAPI, Request, Query, Body, HTTPException
from fastapi.responses import JSONResponse
import turso_serverless
import os
import time
from urllib.parse import parse_qs
from typing import Optional, List

app = FastAPI(title="Vercel + FastAPI")


def get_turso_conn():
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")
    return turso_serverless.connect(url=str(url), auth_token=str(token))


@app.get("/api/sqlite")
def get_data():
    conn = get_turso_conn()
    sql = "SELECT * FROM tv_list"
    rows = conn.execute(sql).fetchall()
    return {"data": rows, "count": len(rows)}


@app.get("/api/sqlite/{id}")
def get_one(id: int):
    conn = get_turso_conn()
    sql = "SELECT * FROM tv_list WHERE id = ?"
    row = conn.execute(sql, (id,)).fetchone()
    if row is None:
        return JSONResponse(status_code=404, content={"error": "not found"})
    return {"data": row}


def mergeLiveSourceList(raw_val: str) -> str:
    return raw_val


@app.get("/api/create_table")
async def create_table():
    conn = get_turso_conn()
    sql = """
        CREATE TABLE IF NOT EXISTS tv_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            yys TEXT NOT NULL,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            uptime INTEGER NOT NULL,
            UNIQUE(yys, name)
        )
    """
    conn.execute(sql)
    return {"code": 200, "msg": "创建数据表成功"}


@app.get("/api/drop_table")
async def drop_table():
    conn = get_turso_conn()
    sql = "DROP TABLE IF EXISTS tv_list"
    conn.execute(sql)
    return {"code": 200, "msg": "删除数据表成功"}


@app.post("/api")
async def api_handler(
    request: Request,
    action: str = Query(...)
):
    content_type = request.headers.get("content-type", "")
    body = {}
    try:
        raw_bytes = await request.body()
        if "application/json" in content_type:
            body = await request.json()
        elif "x-www-form-urlencoded" in content_type:
            raw_str = raw_bytes.decode("utf-8")
            parsed = parse_qs(raw_str)
            body = {k: v[0] for k, v in parsed.items()}
    except Exception:
        pass

    try:
        yys = body.get("yys")
        uptime = int(time.time())
        if not action or not yys:
            raise HTTPException(status_code=400, detail="参数缺失")

        conn = get_turso_conn()

        if action == "save":
            oldName = body.get("old_name")
            newName = body.get("new_name")
            data = body.get("data")
            if not newName:
                raise HTTPException(status_code=400, detail="new_name 不能为空")

            msg = "添加数据成功"
            if oldName and oldName != newName:
                conn.execute(
                    """UPDATE tv_list set content=?, name=?, uptime=? WHERE yys=? AND name=?""",
                    (data, newName, uptime, yys, oldName)
                )
                msg = "修改数据成功"
            else:
                sql = """
                    INSERT INTO tv_list(yys, name, content, uptime)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(yys, name) DO UPDATE SET
                    content = excluded.content,
                    uptime = excluded.uptime
                """
                params = (yys, newName, data, uptime,)
                print("执行SQL:", sql)
                print("绑定参数:", params)
                result = conn.execute(sql, params)
                conn.commit()
                print("本次影响行数:", result.rowcount)
                
            return {"code": 200, "msg": msg}

        elif action == "categorys":
            rows = conn.execute("SELECT id,yys,name FROM tv_list WHERE yys=?", (yys,)).fetchall()
            return {"code": 200, "msg": "获取成功", "data": rows, "count": len(rows)}

        elif action == "merge_list":
            lines: List[str] = []
            rows = conn.execute("SELECT name, content FROM tv_list WHERE yys=?", (yys,)).fetchall()
            for r in rows:
                keyName = r["name"]
                val = r["content"]
                lines.append(keyName[2:] + ",#genre#")
                lines.append(mergeLiveSourceList(val))
            txt = "\n".join(lines)
            conn.execute("""
                INSERT INTO tv_list(yys, name, content, uptime)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(yys,name) DO UPDATE SET
                    content=excluded.content,
                    uptime=excluded.uptime
            """, ("txt", yys, txt, uptime))
            return {"code": 200, "msg": "合并成功", "data": txt}

        elif action == "read":
            file_key = body.get("file")
            if not file_key:
                raise HTTPException(status_code=400, detail="参数缺失：file")
            row = conn.execute(
                "SELECT content FROM tv_list WHERE yys=? AND name=?",
                (yys, file_key)
            ).fetchone()
            val = row["content"] if row else None
            return {"code": 200, "msg": "读取成功", "data": val}

        elif action == "del":
            file_key = body.get("file")
            if not file_key:
                raise HTTPException(status_code=400, detail="参数缺失：file")
            conn.execute(
                "DELETE FROM tv_list WHERE yys=? AND name=?",
                (yys, file_key)
            )
            return {"code": 200, "msg": "删除成功"}

        else:
            raise HTTPException(status_code=400, detail=f"未知操作: {action}")

    except HTTPException:
        raise
    except Exception as e:
        print("[API ERROR]", repr(e))
        raise HTTPException(status_code=500, detail=f"操作失败:{str(e)}")


@app.get("/api")
async def demo(request: Request):
    raw_body = await request.body()
    try:
        json_body = await request.json()
    except Exception:
        json_body = None
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    client_host = request.client.host if request.client else None
    client_port = request.client.port if request.client else None
    method = request.method
    url = str(request.url)
    path = request.url.path
    return {
        "raw_body": raw_body.decode("utf-8", errors="ignore"),
        "json_body": json_body,
        "headers": headers,
        "query_params": query_params,
        "client": {"ip": client_host, "port": client_port},
        "method": method,
        "url": url,
        "path": path
    }


@app.get("/region")
def get_region():
    return {
        "vercel_region": os.environ.get("VERCEL_REGION", "unknown"),
        "vercel_deployment_region": os.environ.get("VERCEL_DEPLOYMENT_REGION", "unknown"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000)
