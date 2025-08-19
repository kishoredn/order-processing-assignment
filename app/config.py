# app/config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_endpoint_url: str = Field("http://localhost:4566", alias="AWS_ENDPOINT_URL")
    aws_region: str = Field("us-east-1", alias="AWS_REGION")
    aws_access_key_id: str = Field("test", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("test", alias="AWS_SECRET_ACCESS_KEY")
    sqs_queue_name: str = Field("orders", alias="SQS_QUEUE_NAME")
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    api_port: int = Field(8000, alias="API_PORT")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
