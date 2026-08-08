from fastapi import FastAPI
from fastapi.responses import JSONResponse
import turso_serverless
import os
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# 必须在 getenv 前面！
load_dotenv()  



os.system("clear")


app = FastAPI(title="Vercel + FastAPI")

#TURSO_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODU5NjkyODQsImlkIjoiMDE5ZmQ0MTAtOTMwMS03OGUyLTk4OWYtOThlMmRmMDg3ZjU1Iiwia2lkIjoiVlg4M05ETndSLTRCT2xQN2VHUnNROHlEczZsN3dQWXdTc0hPX1E1bncwTSIsInJpZCI6ImRjNThkOWM0LTliYmYtNDRiZC05NTc5LTgwMmExNDdhMDc2OCJ9.nzp6aOky4Mbp6JkiomFjP9UOCriUrHPlluBwj71Vn6PHiKWS0gQZ8shjMoNj-LeqXV4JYZtEOqZxrB1HXVl0Ag"
#TURSO_DATABASE_URL = "libsql://database-almond-marble-vercel-icfg-uqzxpveymdpzrjnfg6z1gvz1.aws-ap-northeast-1.turso.io"

conn = None

@app.on_event("startup")
async def init_db():
    global conn
    env_url=os.getenv("TURSO_DATABASE_URL")
    env_token=os.getenv("TURSO_AUTH_TOKEN")
    print(env_url)
    
    conn = turso_serverless.connect(
        url=str(env_url),
        auth_token=str(env_token)
    )


@app.get("/api/sqlite")
def get_data():
    sql = "SELECT * FROM tv_list"
    rows = conn.execute(sql).fetchall()  # ← 这里取数据
    
    # rows 是 list[dict]，FastAPI 自动转 JSON
    return {"data": rows, "count": len(rows)}

@app.get("/api/sqlite/{id}")
def get_one(id: int):
    sql = "SELECT * FROM tv_list WHERE id = ?"
    row = conn.execute(sql, (id,)).fetchone()  # ← 取单条
    
    if row is None:
        return JSONResponse(status_code=404, content={"error": "not found"})
    
    return {"data": row}
import os


from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import Optional, List







# -------------------------- 模拟你原有 merge 函数，自行替换源码 --------------------------
def mergeLiveSourceList(raw_val: str) -> str:
    # 这里直接粘贴你原来 JS 的 mergeLiveSourceList 逻辑转Python
    return raw_val



@app.get("/api/create_table")
async def create_table():
    sql ="""
        CREATE TABLE IF NOT EXISTS tv_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT
            yys TEXT NOT NULL,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            update INTEGER NOT NULL,
            UNIQUE(yys, name)
        )
    """
    conn.execute(sql)
    return {"code":200, "msg":"创建数据表成功"}


@app.get("/api/drop_table")
async def create_table():
    sql = "DROP TABLE IF EXISTS tv_list"
    conn.execute(sql)
    return {"code":200, "msg":"删除数据表成功"}




# -------------------------- 统一接口 /api --------------------------
@app.post("/api")
async def api_handler(
    action: str = Query(...),
    body: dict = Body(...)
):
    try:
        yys = body.get("yys")
        if not action or not yys:
            raise HTTPException(status_code=400, detail={"code":400, "msg":"参数缺失"})

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if action == "save":
            oldName = body.get("old_name")
            newName = body.get("new_name")
            data = body.get("data")
            if not newName:
                raise HTTPException(status_code=400, detail={"code":400, "msg":"new_name 不能为空"})

            msg = "添加数据成功"
            # 旧名称存在且不等于新名称 → 删除旧记录
            if oldName and oldName != newName:
                cur.execute("DELETE FROM kv_store WHERE yys=? AND item_key=?", (yys, oldName))
                msg = "修改数据成功"
            # upsert 写入新数据
            cur.execute("""
                INSERT INTO kv_store(yys, item_key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(yys, item_key) DO UPDATE SET value=excluded.value
            """, (yys, newName, data))
            conn.commit()
            return {"code":200, "msg":msg}

        elif action == "categorys":
            cur.execute("SELECT item_key FROM kv_store WHERE yys=?", (yys,))
            rows = cur.fetchall()
            lst = [{"name": r["item_key"]} for r in rows]
            return {"code":200, "msg":"获取成功", "data":lst}

        elif action == "merge_list":
            lines: List[str] = []
            cur.execute("SELECT item_key, value FROM kv_store WHERE yys=?", (yys,))
            rows = cur.fetchall()
            for r in rows:
                keyName = r["item_key"]
                val = r["value"]
                lines.append(keyName[2:] + ",#genre#")
                lines.append(mergeLiveSourceList(val))
            txt = "\n".join(lines)
            # 原逻辑：["txt", yys] → 存 yys="txt", item_key=yys
            cur.execute("""
                INSERT INTO kv_store(yys, item_key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(yys, item_key) DO UPDATE SET value=excluded.value
            """, ("txt", yys, txt))
            conn.commit()
            return {"code":200, "msg":"合并成功", "data":txt}

        elif action == "read":
            file_key = body.get("file")
            if not file_key:
                raise HTTPException(status_code=400, detail={"code":400, "msg":"参数缺失：file"})
            cur.execute("SELECT value FROM kv_store WHERE yys=? AND item_key=?", (yys, file_key))
            row = cur.fetchone()
            if not row:
                val = None
            else:
                val = row["value"]
            return {"code":200, "msg":"读取成功", "data":val}

        elif action == "del":
            file_key = body.get("file")
            if not file_key:
                raise HTTPException(status_code=400, detail={"code":400, "msg":"参数缺失：file"})
            cur.execute("DELETE FROM kv_store WHERE yys=? AND item_key=?", (yys, file_key))
            conn.commit()
            return {"code":200, "msg":"删除成功"}

        else:
            raise HTTPException(status_code=400, detail={"code":400, "msg":f"未知操作: {action}"})

    except HTTPException:
        raise
    except Exception as e:
        print("[API ERROR]", str(e))
        raise HTTPException(status_code=500, detail={"code":500, "msg":"操作失败"})
    finally:
        if "conn" in locals():
            conn.close()





@app.get("/api")
async def demo(request: Request):
    # 1.原始字节body
    raw_body = await request.body()

    # 2.解析json（Content-Type:application/json）
    try:
        json_body = await request.json()
    except Exception:
        json_body = None

    # 3.解析表单 form‑data / x‑www‑form‑urlencoded
    #form_data = await request.form()

    # 4.请求头
    headers = dict(request.headers)

    # 5.查询参数
    query_params = dict(request.query_params)

    # 6.客户端信息
    client_host = request.client.host if request.client else None
    client_port = request.client.port if request.client else None

    # 7.请求方法、url、路径
    method = request.method
    url = str(request.url)
    path = request.url.path

    return {
        "raw_body": raw_body.decode("utf‑8", errors="ignore"),
        "json_body": json_body,
        #"form_data": dict(form_data),
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



	
app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app="main:app", host="0.0.0.0", port=8000)

	