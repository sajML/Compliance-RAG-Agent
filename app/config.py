from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    chroma_host: Optional[str] = None
    chroma_port: int = 8000
    chroma_ssl: bool = False
    chroma_token: Optional[str] = None
    chroma_persist_dir: str = "./chroma_data"
    collection_name: str = "compliance_docs"

    chunk_size: int = 512
    chunk_overlap: int = 64
    max_pdf_pages: int = 100

    retrieval_top_k: int = 10
    final_top_k: int = 5

    max_file_size_mb: int = 50

    api_key: Optional[str] = None

    # UI login (session-cookie auth for the web UI). Programmatic callers still use api_key.
    app_username: Optional[str] = None
    app_password: Optional[str] = None
    session_secret: Optional[str] = None
    cookie_secure: bool = True  # set false only for local http preview

    model_config = {"env_file": ".env", "extra": "ignore"}

    def require_api_key(self) -> str:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        return self.openai_api_key


settings = Settings()
