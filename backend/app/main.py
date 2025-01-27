from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_router
from app.config.settings import settings
from app.api.middleware.error_handler import error_handler
from app.api.middleware.request_logger import request_logger

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册中间件
app.middleware("http")(error_handler)
app.middleware("http")(request_logger)

# 正确注册了路由
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to AI MindMap API"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=settings.DEBUG) 