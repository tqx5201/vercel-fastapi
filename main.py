from fastapi import FastAPI
from fastapi.responses import JSONResponse
import turso_serverless
import os
from fastapi.staticfiles import StaticFiles

os.system("clear")


app = FastAPI(title="Vercel + FastAPI")

TURSO_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODU5NjkyODQsImlkIjoiMDE5ZmQ0MTAtOTMwMS03OGUyLTk4OWYtOThlMmRmMDg3ZjU1Iiwia2lkIjoiVlg4M05ETndSLTRCT2xQN2VHUnNROHlEczZsN3dQWXdTc0hPX1E1bncwTSIsInJpZCI6ImRjNThkOWM0LTliYmYtNDRiZC05NTc5LTgwMmExNDdhMDc2OCJ9.nzp6aOky4Mbp6JkiomFjP9UOCriUrHPlluBwj71Vn6PHiKWS0gQZ8shjMoNj-LeqXV4JYZtEOqZxrB1HXVl0Ag"
TURSO_DATABASE_URL = "libsql://database-almond-marble-vercel-icfg-uqzxpveymdpzrjnfg6z1gvz1.aws-ap-northeast-1.turso.io"

conn = None

@app.on_event("startup")
async def init_db():
    global conn
    conn = turso_serverless.connect(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
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

	
app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app="main:app", host="0.0.0.0", port=8000)

	