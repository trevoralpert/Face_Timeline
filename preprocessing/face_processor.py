import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

class FaceProcessor:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            min_detection_confidence=0.5
        )

    def process_image(self, image_path: str, output_size: Tuple[int, int] = (512, 512)) -> Optional[np.ndarray]:
        """
        Process an image to detect, align, and crop the face.
        
        Args:
            image_path: Path to the input image
            output_size: Desired output size (width, height)
            
        Returns:
            Processed face image or None if no face detected
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Could not read image: {image_path}")
                return None
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect face
            results = self.face_detection.process(image_rgb)
            if not results.detections:
                logging.warning(f"No face detected in image: {image_path}")
                return None
            
            # Get face bounding box
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = image.shape
            x, y = int(bbox.xmin * w), int(bbox.ymin * h)
            width, height = int(bbox.width * w), int(bbox.height * h)
            
            # Add margin
            margin = 0.5  # 50% margin
            x = max(0, int(x - width * margin/2))
            y = max(0, int(y - height * margin/2))
            width = min(w - x, int(width * (1 + margin)))
            height = min(h - y, int(height * (1 + margin)))
            
            # Crop face
            face = image[y:y+height, x:x+width]
            
            # Resize
            face_resized = cv2.resize(face, output_size)
            
            return face_resized
            
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {str(e)}")
            return None

    def process_directory(self, input_dir: str, output_dir: str):
        """
        Process all images in a directory.
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save processed images
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for img_path in input_path.glob("*.[jJ][pP][gG]"):
            processed = self.process_image(str(img_path))
            if processed is not None:
                output_file = output_path / f"processed_{img_path.name}"
                cv2.imwrite(str(output_file), processed)
                logging.info(f"Processed {img_path.name}")
            else:
                logging.warning(f"Failed to process {img_path.name}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    processor = FaceProcessor()
    processor.process_directory("data/raw", "data/processed") 