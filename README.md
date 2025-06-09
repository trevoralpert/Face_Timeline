# Face Timeline (Age Progression Timeline)

An interactive web application for visualizing age progression through a dynamic, scrollable timeline of your photos. Built with **Streamlit** and **FastAPI** for rapid prototyping and user-friendly interaction.

## Features

- **Photo Upload & Date Assignment**: Upload multiple photos, assign a date to each (year required, month/day optional).
- **EXIF Date Extraction**: Automatically extracts "date taken" from photo metadata (including HEIC support via `pillow-heif`).
- **Horizontal, Proportional Timeline**: Displays a scrollable timeline where images are spaced to scale by date. Labels reflect date granularity (year, year-month, or year-month-day).
- **Image Compression**: All images are compressed (max 800px, JPEG quality 50) to stay under Streamlit's 200MB message size limit.
- **Remove & Reset**: Remove individual images or reset the entire upload list.
- **Import/Export Timeline**: Export your timeline as a ZIP (images, CSV mapping, and PNG timeline). Import a ZIP to restore a timeline, preserving date granularity.
- **Duplicate Filename Handling**: Exported images with the same date get unique filenames (e.g., `_2`, `_3`, etc.).
- **Dock Magnification Effect**: Select a photo to magnify with a slider; the selected photo is shown larger in the timeline and in a fixed magnification window above.
- **Birthday & Age Calculation**: Enter your birthday to see your age at each photo. The magnification slider and timeline display ages.
- **User-Friendly UI**: Timeline, magnification window, and slider are at the top for easy access. Robust handling of large image batches and optional date fields.

## Project Structure

```
├── streamlit_app.py        # Main Streamlit app
├── requirements.txt        # Python dependencies
├── api/                   # FastAPI backend (optional for advanced features)
├── preprocessing/         # (Optional) Scripts for photo preprocessing
├── ml/                    # (Optional) Machine learning models
├── data/                  # Data storage
```

## Technical Stack

- **Frontend/UI**: Streamlit
- **Backend**: FastAPI (for advanced/AI features)
- **Image Processing**: Pillow, pillow-heif, OpenCV, MediaPipe
- **ML/AI (optional)**: PyTorch, Stable Diffusion, InsightFace, etc.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/trevoralpert/Face_Timeline.git
   cd Face_Timeline
   ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - For HEIC image support, `pillow-heif` is included in requirements.
3. **(Optional) Install and run the FastAPI backend** if you want advanced AI features:
   ```bash
   cd api
   uvicorn main:app --reload
   ```
4. **Run the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage

- **Upload photos** (JPEG, PNG, HEIC). Assign dates as prompted. EXIF dates are auto-filled if available.
- **Adjust the timeline**: Use the slider to magnify a photo and see your age at the time (if birthday is set).
- **Remove or reset**: Remove individual photos or reset all uploads.
- **Export**: Download a ZIP with your timeline images, a CSV mapping, and a PNG of the timeline.
- **Import**: Restore a timeline by uploading a previously exported ZIP.

## Notes
- All image processing is done client-side for privacy and speed.
- The app is optimized for rapid prototyping and user experience.
- For large batches, ensure total image size stays under 200MB (Streamlit limit).

## License

MIT License - See LICENSE file for details 