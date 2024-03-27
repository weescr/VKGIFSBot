from fastapi import FastAPI
from src.config import settings, Settings
from starlette.middleware.cors import CORSMiddleware
from src import list_of_routes

def bind_routes(application: FastAPI, settings: Settings) -> None:
    """
    Bind all routes to application.
    """
    for route in list_of_routes:
        application.include_router(route, prefix=settings.PATH_PREFIX)


def get_app() -> FastAPI:
    """
    Creates application and all dependable objects.
    """
    description = """"""

    application = FastAPI(
        title="VKGIFSBot",
        description=description,
        docs_url=settings.SWAGGER_URL,
        openapi_url=settings.OPENAPI,
        redoc_url=None,
        version="3.0.0",
    )
    bind_routes(application, settings)
    application.state.settings = settings
    return application


app_fastapi = get_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app_fastapi", host=settings.SERVER_HOST, port=settings.SERVER_PORT)