import logging
import os
from types import FrameType
from typing import cast

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # return {"message": "Hello World"}
    return templates.TemplateResponse(
        request=request, name="index.html"
    )


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # noqa: WPS609
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage(),
        )





def start(port):
    global config
    config= uvicorn.Config("fastApi:app", host='127.0.0.1', port=port, reload=False)
    global webServer
    webServer = uvicorn.Server(config)

    # 将uvicorn输出的全部让loguru管理
    LOGGER_NAMES = ("uvicorn.asgi", "uvicorn.access", "uvicorn")

    # change handler for default uvicorn logger
    logging.getLogger().handlers = [InterceptHandler()]
    for logger_name in LOGGER_NAMES:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    webServer.run()
    # uvicorn.run(app="fastApi:app", host="127.0.0.1", port=port, reload=False)


# if __name__ == '__main__':

    # uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
