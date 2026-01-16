from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    # --- 配置区域 ---
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000")) # <--- 在这里修改端口号，例如改为 8080
    reload = os.getenv("RELOAD", "1") not in {"0", "false", "False"}
    # ----------------

    uvicorn.run("app.main:app", host=host, port=port, reload=reload)

