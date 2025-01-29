# # No Third person except AI-Team is allowed to run this code. No changes in this code are allowed except by approval from AI Team
# # Moderation API will be implemented once This application will be in production.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import generate_post, process_image, regenerate_image, bulk_post_generation, regenerate_post, test, websocket_health

app = FastAPI()

origins = ["*"] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_post.router, prefix="/api", tags=["Generate Post"])
app.include_router(regenerate_image.router, prefix="/api", tags=["Regenerate Image"])
app.include_router(regenerate_post.router, prefix="/api", tags=["Regenerate Post"])
app.include_router(process_image.router, prefix="/api", tags=["Process Image"])
app.include_router(bulk_post_generation.router, prefix="/api", tags=["Bulk Post Generation"])
app.include_router(websocket_health.router, prefix="/api", tags=["Websocket Health"])
app.include_router(test.router, prefix="/test", tags=["Test"])