from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.root_node import router as get_root
from routes.child_node import router as get_child

app = FastAPI()

# allowing everything for dev environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

app.include_router(get_root, prefix='/api')
app.include_router(get_child, prefix='/api')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)