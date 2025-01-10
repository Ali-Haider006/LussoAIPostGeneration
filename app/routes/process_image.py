from fastapi import APIRouter, Form
from app.services.image_processing import remove_background, extract_color_proportions
from app.utils.download_image_from_url import download_image_from_url
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/process-image/")
async def process_image(file: str = Form(...),):
    try:
        image_bytes = await download_image_from_url(file)
        image_no_bg = remove_background(image_bytes)
        color_proportions = extract_color_proportions(image_no_bg)
        return JSONResponse(content={"colors": color_proportions})
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"Unexpected error: {str(e)}"}, status_code=500)
    