# server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.root_node import router as get_root
from routes.child_node import router as get_child
from routes.sources import router as sources

# DB init
from sqlalchemy.ext.asyncio import AsyncEngine
from db.context import get_engine as get_graph_engine
from db.models import Base as GraphBase
from registry.session import registry_engine
from registry.models import Base as RegistryBase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

app.include_router(get_root,  prefix='/api')
app.include_router(get_child, prefix='/api')
app.include_router(sources,   prefix='/api')

@app.on_event("startup")
async def on_startup():
    # create tables for both databases
    graph_engine: AsyncEngine = get_graph_engine()
    async with graph_engine.begin() as conn:
        await conn.run_sync(GraphBase.metadata.create_all)

    async with registry_engine.begin() as conn:
        await conn.run_sync(RegistryBase.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
