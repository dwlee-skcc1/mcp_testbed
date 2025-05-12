from contextlib import AsyncExitStack
from fastapi import FastAPI
from starlette.routing import Mount

from mcpserver.document import document_app
from mcpserver.database import database_app

async def combined_lifespan(app):
    async with AsyncExitStack() as stack:
        # document_app의 lifespan 실행
        await stack.enter_async_context(document_app.router.lifespan_context(app))
        # database_app의 lifespan 실행
        await stack.enter_async_context(database_app.router.lifespan_context(app))
        yield

app = FastAPI(
    routes=[
        Mount("/document", app=document_app),
        Mount("/database", app=database_app),
    ],
    lifespan=combined_lifespan,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)