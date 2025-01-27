import os
import sys

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

import uvicorn
from app.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[os.path.join(ROOT_DIR, "app")],
        workers=1
    ) 