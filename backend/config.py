from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://autism_user:autism_pass@db:5432/autism_db"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32"
    VIDEO_STORAGE_PATH: str = "/data/videos"
    S3_BUCKET: str = "autism-sessions"
    S3_ENDPOINT: str = ""  # leave empty for AWS, set for MinIO
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    OPENFACE_BIN: str = "openface"
    ASDMOTION_PATH: str = "/opt/ASDMotion"
    MODEL_PATH: str = "/app/ml/questionnaire_model.pkl"
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
