import os
import uvicorn

from app.core.settings import settings


def main() -> None:
    workers = int(os.getenv("UVICORN_WORKERS", "1"))
    proxy_headers = os.getenv("UVICORN_PROXY_HEADERS", "true").lower() == "true"
    forwarded_allow_ips = os.getenv("UVICORN_FORWARDED_ALLOW_IPS", "*")
    log_level = os.getenv("UVICORN_LOG_LEVEL", "info")
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=workers,
        proxy_headers=proxy_headers,
        forwarded_allow_ips=forwarded_allow_ips,
        log_level=log_level,
        reload=reload,
    )


if __name__ == "__main__":
    main()
