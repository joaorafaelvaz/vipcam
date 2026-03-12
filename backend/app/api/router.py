from fastapi import APIRouter

from app.api import analytics, cameras, emotions, persons, settings

api_router = APIRouter()

api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(persons.router, prefix="/persons", tags=["persons"])
api_router.include_router(emotions.router, prefix="/emotions", tags=["emotions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])


@api_router.get("/health")
async def health_check():
    return {"status": "ok"}
