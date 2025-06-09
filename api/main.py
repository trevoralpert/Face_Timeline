from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import sys
import logging
from typing import List
import os

# Add parent directory to path to import preprocessing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing.face_processor import FaceProcessor

app = FastAPI(title="Age Progression Timeline API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize face processor
face_processor = FaceProcessor()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure data directories exist
UPLOAD_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/upload-images/")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Upload multiple images for processing.
    """
    try:
        saved_files = []
        for file in files:
            # Save uploaded file
            file_path = UPLOAD_DIR / file.filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            
            # Process the image
            processed = face_processor.process_image(str(file_path))
            if processed is not None:
                output_path = PROCESSED_DIR / f"processed_{file.filename}"
                cv2.imwrite(str(output_path), processed)
                logger.info(f"Successfully processed {file.filename}")
            else:
                logger.warning(f"Failed to process {file.filename}")
        
        return {"message": f"Successfully uploaded and processed {len(saved_files)} images"}
    
    except Exception as e:
        logger.error(f"Error processing uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processed-images/")
async def list_processed_images():
    """
    List all processed images.
    """
    try:
        images = [f.name for f in PROCESSED_DIR.glob("*.jpg")]
        return {"images": images}
    except Exception as e:
        logger.error(f"Error listing processed images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/image/{image_name}")
async def get_image(image_name: str):
    """
    Retrieve a processed image by name.
    """
    try:
        image_path = PROCESSED_DIR / image_name
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(str(image_path))
    except Exception as e:
        logger.error(f"Error retrieving image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 