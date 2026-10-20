"""Router registry.

Phase: Step 2 (cities and cinemas APIs).
Will hold: include_routers(app). Adds every feature router under /api/v1.
A new feature means one new line here.
"""

# one place for all routes.

from fastapi import FastAPI, APIRouter

def include_routers(app: FastAPI):
    api= APIRouter(prefix="/api")
    
    @api.get("/health")
    async def health()-> dict[str,str]:
        return {"status": "ok"}
    
    app.include_router(api)