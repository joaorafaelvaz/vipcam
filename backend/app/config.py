from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://vipcam:changeme@db:5432/vipcam"
    # Redis
    redis_url: str = "redis://redis:6379/0"

    # GPU / Models
    cuda_visible_devices: str = "0"
    yolo_model_path: str = "/models/yolov8x.pt"
    yolo_imgsz: int = 1280
    yolo_conf: float = 0.5
    insightface_model_name: str = "buffalo_l"
    insightface_det_size: int = 640
    hsemotion_model_name: str = "enet_b2_8"

    # Face matching
    face_match_threshold: float = 0.4
    face_quality_min: float = 0.5
    face_max_embeddings_per_person: int = 5

    # Emotion
    emotion_ema_alpha: float = 0.3
    emotion_shift_min_frames: int = 3

    # Processing
    processing_fps_target: int = 5
    scene_change_threshold: float = 0.03
    enable_pipeline: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret: str = "trocar_por_chave_segura_longa"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cors_origins: list[str] = ["http://localhost:3000"]

    # Storage
    snapshot_dir: str = "/data/snapshots"
    face_crop_dir: str = "/data/face_crops"
    max_snapshots: int = 10000


settings = Settings()
