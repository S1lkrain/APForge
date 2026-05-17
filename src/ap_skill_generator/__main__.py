from ap_skill_generator.api import app
from ap_skill_generator.config import Settings
from ap_skill_generator.logging_utils import configure_logging

import uvicorn


def main() -> None:
    configure_logging()
    settings = Settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
