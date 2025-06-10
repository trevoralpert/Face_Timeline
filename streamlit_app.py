import streamlit as st
import requests
from PIL import Image, UnidentifiedImageError
import io
import random
import datetime
import base64
from io import BytesIO
import zipfile
import csv
from PIL import ExifTags
import pillow_heif
from PIL import ImageDraw, ImageFont
pillow_heif.register_heif_opener()

# Utility function for image to base64 (needed for timeline rendering)
def image_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

st.set_page_config(page_title="Age Progression Timeline", layout="wide")

# User birthday input (must be before any use)
st.markdown('### User Info')
user_birthday = st.date_input("Enter your birthday", min_value=datetime.date(1950, 1, 1), key="user_birthday")

BACKEND_URL = "http://localhost:8000"

st.title("Age Progression Timeline (Flexible Date Input)")

# --- Timeline and magnification window at the top ---
photo_files = st.session_state.photo_files if "photo_files" in st.session_state else []
if photo_files:
    # Build photo_dates for timeline display only (do not use widget state here)
    photo_dates = []
    current_year = datetime.date.today().year
    prev_date = None
    for i, file_dict in enumerate(photo_files):
        imported = file_dict.get("imported", False)
        imported_year = file_dict.get("date").year if imported and file_dict.get("date") else None
        imported_month = file_dict.get("month") if imported else None
        imported_day = file_dict.get("day") if imported else None
        imported_month_specified = file_dict.get("month_specified") if imported else False
        imported_day_specified = file_dict.get("day_specified") if imported else False
        exif_year = file_dict.get("exif_year")
        exif_month = file_dict.get("exif_month")
        exif_day = file_dict.get("exif_day")
        if prev_date is not None:
            default_date = prev_date + datetime.timedelta(days=1)
        else:
            default_date = datetime.date.today()
        year_options = list(range(1950, current_year+1))
        if imported_year and imported_year in year_options:
            year = imported_year
        elif exif_year and exif_year in year_options:
            year = exif_year
        else:
            year = default_date.year
        if imported_month_specified and imported_month:
            month = imported_month
            month_specified = True
        elif exif_month:
            month = exif_month
            month_specified = True
        else:
            month = None
            month_specified = False
        if imported_day_specified and imported_day:
            day = imported_day
            day_specified = True
        elif exif_day:
            day = exif_day
            day_specified = True
        else:
            day = None
            day_specified = False
        if not month_specified:
            date = datetime.date(int(year), 1, 1)
            display_str = f"{year}--"
        elif month_specified and not day_specified:
            date = datetime.date(int(year), int(month), 1)
            display_str = f"{year}-{int(month):02d}-"
        else:
            date = datetime.date(int(year), int(month), int(day)) if day_specified else datetime.date(int(year), int(month), 1)
            display_str = date.strftime("%Y-%m-%d") if day_specified else f"{year}-{int(month):02d}"
        photo_dates.append({"file_dict": file_dict, "date": date, "display": display_str, "month_specified": month_specified, "day_specified": day_specified, "month": int(month) if month_specified else None, "day": int(day) if day_specified else None})
        prev_date = date
    # Sort by date
    photo_dates.sort(key=lambda x: x["date"])
    # --- Horizontal, scrollable, proportional timeline with gap markers ---
    min_date = min([x["date"] for x in photo_dates])
    max_date = max([x["date"] for x in photo_dates])
    total_days = (max_date - min_date).days or 1
    GAP_THRESHOLD = 730  # days (2 years)
    # Calculate ages for each photo
    ages = []
    for pd in photo_dates:
        if user_birthday:
            age_years = (pd["date"] - user_birthday).days / 365.25
            ages.append(age_years)
        else:
            ages.append(None)
    # (Removed duplicate timeline/magnification block here. See later in file for main timeline UI.)

# Clean up session state if old UploadedFile objects are present
if "photo_files" in st.session_state:
    if any(not isinstance(f, dict) for f in st.session_state.photo_files):
        st.session_state.photo_files = []

if "photo_files" not in st.session_state:
    st.session_state.photo_files = []

# Add a flag to track if a ZIP has been imported
if "zip_imported" not in st.session_state:
    st.session_state["zip_imported"] = False

if st.button("Reset Uploaded Photos"):
    st.session_state.photo_files = []
    st.session_state["zip_imported"] = False

uploaded_files = st.file_uploader(
    "Upload your timeline photos", type=["jpg", "jpeg", "png", "heic"], accept_multiple_files=True
)

def compress_image(file_bytes, max_dim=800, quality=50):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        # Resize if very large
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.size[0]*ratio), int(img.size[1]*ratio))
            img = img.resize(new_size, Image.LANCZOS)
        else:
            new_size = img.size
        buf = io.BytesIO()
        img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue(), new_size
    except Exception as e:
        st.warning(f"Could not compress image: {e}")
        return file_bytes, None

def get_exif_date(file_bytes):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        exif = img._getexif()
        if not exif:
            return None
        for tag, value in exif.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "DateTimeOriginal":
                # Format: 'YYYY:MM:DD HH:MM:SS'
                date_str = value.split(' ')[0]
                parts = date_str.split(':')
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    return year, month, day
    except Exception:
        pass
    return None

# Always compress on upload
if uploaded_files:
    for file in uploaded_files:
        if not any(f["name"] == file.name for f in st.session_state.photo_files):
            file_bytes = file.getvalue()
            compressed_bytes, new_size = compress_image(file_bytes)
            exif_date = get_exif_date(file_bytes)
            file_dict = {
                "name": file.name,
                "bytes": compressed_bytes,
                "type": "image/jpeg"
            }
            if exif_date:
                year, month, day = exif_date
                file_dict["exif_year"] = year
                file_dict["exif_month"] = month
                file_dict["exif_day"] = day
            st.info(f"Compressed {file.name} to {len(compressed_bytes)//1024} KB" + (f" (resized to {new_size[0]}x{new_size[1]})" if new_size else ""))
            st.session_state.photo_files.append(file_dict)

# After all uploads, check total size
if st.session_state.photo_files:
    total_bytes = sum(len(f["bytes"]) for f in st.session_state.photo_files)
    if total_bytes > 200 * 1024 * 1024:
        st.warning(f"Total image data is {total_bytes//1024//1024} MB, which may exceed Streamlit's message size limit. Please remove some images or compress further.")

photo_files = st.session_state.photo_files

if photo_files:
    st.write("For each photo, enter the date it was taken (year required, month/day optional). Remove photos here if needed.")
    remove_names = []
    photo_dates = []
    current_year = datetime.date.today().year
    prev_date = None
    for i, file_dict in enumerate(photo_files):
        col1, col2 = st.columns([1, 2])
        with col1:
            try:
                img = Image.open(io.BytesIO(file_dict["bytes"]))
                st.image(img, width=100)
            except UnidentifiedImageError:
                st.warning(f"Could not open image: {file_dict['name']}")
            # Use index and filename as key for uniqueness
            if st.button("Remove", key=f"remove_date_{i}_{file_dict['name']}"):
                remove_names.append(file_dict["name"])
        with col2:
            # --- Use imported date info if present ---
            imported = file_dict.get("imported", False)
            imported_year = file_dict.get("year")
            imported_month = file_dict.get("month")
            imported_day = file_dict.get("day")
            imported_month_specified = file_dict.get("month_specified", False)
            imported_day_specified = file_dict.get("day_specified", False)
            exif_year = file_dict.get("exif_year")
            exif_month = file_dict.get("exif_month")
            exif_day = file_dict.get("exif_day")

            if prev_date is not None:
                default_date = prev_date + datetime.timedelta(days=1)
            else:
                default_date = datetime.date.today()
            year_options = list(range(1994, current_year+1))
            # --- Default year: imported if present, else EXIF, else prev/now ---
            if imported_year and imported_year in year_options:
                default_year_idx = year_options.index(imported_year)
            elif exif_year and exif_year in year_options:
                default_year_idx = year_options.index(exif_year)
            else:
                default_year_idx = year_options.index(default_date.year) if default_date.year in year_options else 0
            year = st.selectbox(f"Year for photo {i+1}", options=year_options, index=default_year_idx, key=f"year_{i}")

            month_options = ["(None)"] + list(range(1, 13))
            # --- Default month: imported if present, else EXIF, else none ---
            if imported_month_specified and imported_month:
                default_month_idx = month_options.index(imported_month)
            elif exif_month:
                default_month_idx = month_options.index(exif_month)
            else:
                default_month_idx = 0
            month = st.selectbox(f"Month (optional) for photo {i+1}", options=month_options, index=default_month_idx, key=f"month_{i}")
            month_specified = month != "(None)"
            day = None
            day_specified = False
            if month_specified:
                days_in_month = 31
                try:
                    days_in_month = (datetime.date(int(year), int(month)%13, 1) - datetime.timedelta(days=1)).day if int(month) == 12 else (datetime.date(int(year), int(month)+1, 1) - datetime.timedelta(days=1)).day
                except Exception:
                    pass
                # --- Default day: imported if present, else EXIF, else blank ---
                day_key = f"day_{i}"
                if imported_day_specified and imported_day:
                    day_val = str(imported_day)
                elif exif_day:
                    day_val = str(exif_day)
                else:
                    day_val = ""
                day = st.text_input(f"Day (optional) for photo {i+1}", value=day_val, key=day_key, max_chars=2, help="Leave blank for no day")
                if day and day.isdigit() and 1 <= int(day) <= days_in_month:
                    day_specified = True
                    day = int(day)
                else:
                    day = None
            # Compose display string and store what was specified
            if not month_specified:
                date = datetime.date(int(year), 1, 1)
                display_str = f"{year}--"
            elif month_specified and not day_specified:
                date = datetime.date(int(year), int(month), 1)
                display_str = f"{year}-{int(month):02d}-"
            else:
                date = datetime.date(int(year), int(month), int(day)) if day_specified else datetime.date(int(year), int(month), 1)
                display_str = date.strftime("%Y-%m-%d") if day_specified else f"{year}-{int(month):02d}"
            # --- Persist date info in session state ---
            file_dict["year"] = int(year)
            file_dict["month"] = int(month) if month_specified else None
            file_dict["day"] = int(day) if day_specified else None
            file_dict["month_specified"] = month_specified
            file_dict["day_specified"] = day_specified
            file_dict["date"] = date
            file_dict["display"] = display_str
            prev_date = date
        photo_dates.append({"file_dict": file_dict, "date": file_dict["date"], "display": file_dict["display"], "month_specified": file_dict["month_specified"], "day_specified": file_dict["day_specified"], "month": file_dict["month"], "day": file_dict["day"]})
    # Actually remove after the loop (to avoid index issues)
    if remove_names:
        st.session_state.photo_files = [f for f in st.session_state.photo_files if f["name"] not in remove_names]
        st.rerun()

    # Do NOT sort photo_dates; preserve upload order

    # Add a slider to select the magnified photo, labeled by age
    selected_idx = st.slider("Magnified photo (by age)", 0, len(photo_dates)-1, 0, key="magnified_photo_slider")

    # Magnification window above the timeline
    selected_file_dict = photo_dates[selected_idx]["file_dict"]
    selected_age = ages[selected_idx] if user_birthday else None
    try:
        mag_img = Image.open(io.BytesIO(selected_file_dict["bytes"]))
        mag_img_b64 = image_to_base64(mag_img)
    except UnidentifiedImageError:
        mag_img_b64 = ""
    age_html = f"<div style='text-align:center; font-size:20px; color:#444; margin-top:12px;'>Age {selected_age:.1f}</div>" if selected_age is not None else ""
    magnify_html = f'''
    <div style="display: flex; flex-direction: column; align-items: center; height: 340px;">
      <div style="width: 260px; height: 260px; border: 4px solid #222; border-radius: 24px; box-shadow: 0 8px 32px #aaa; background: #fff; display: flex; align-items: center; justify-content: center;">
        <img src="data:image/png;base64,{mag_img_b64}" style="max-width: 240px; max-height: 240px; border-radius: 16px;">
      </div>
      {age_html}
    </div>
    '''
    st.markdown(magnify_html, unsafe_allow_html=True)

    html = "<div style='display: flex; overflow-x: auto; align-items: flex-end; height: 260px; padding-bottom: 16px;'>"
    for i, pd in enumerate(photo_dates):
        file_dict = pd["file_dict"]
        date = pd["date"]
        # Use robust label logic with padding for alignment
        if not pd["month_specified"]:
            label = f"{date.year}--"
        elif pd["month_specified"] and not pd["day_specified"]:
            label = f"{date.year}-{pd['month']:02d}-"
        else:
            label = f"{date.year}-{pd['month']:02d}-{pd['day']:02d}"
        try:
            img = Image.open(io.BytesIO(file_dict["bytes"]))
            img_b64 = image_to_base64(img)
        except UnidentifiedImageError:
            img_b64 = ""
        # Magnify the selected photo
        if i == selected_idx:
            img_style = "width:160px; border-radius:16px; box-shadow:0 4px 16px #aaa; z-index:2;"
            label_style = "font-size:16px; font-weight:bold; color:#222;"
        else:
            img_style = "width:80px; border-radius:8px; box-shadow:0 2px 8px #aaa; z-index:1;"
            label_style = "font-size:12px; color:#444;"
        # Show age under each photo if birthday is set
        age_str = f"<div style='font-size:12px; color:#888;'>{'Age %.1f' % ages[i] if ages[i] is not None else ''}</div>" if user_birthday else ""
        html += f"""<div style='text-align: center;'>
            <img src='data:image/png;base64,{img_b64}' style='{img_style}'><br>
            <span style='{label_style}'>{label}</span>
            {age_str}
        </div>"""
        if i < len(photo_dates) - 1:
            days_gap = (photo_dates[i+1]["date"] - pd["date"]).days
            px_gap = int(40 + 300 * days_gap / total_days)
            if days_gap > GAP_THRESHOLD:
                html += f"""
                <div style='display: flex; flex-direction: column; align-items: center; width:{px_gap}px;'>
                    <div style='border-bottom: 2px dashed #e74c3c; width: 80%; margin: 0 auto 4px auto;'></div>
                    <span style='color: #e74c3c; font-size: 12px;'>Gap: {days_gap//365} yr</span>
                </div>
                """
            else:
                html += f"<div style='width:{px_gap}px;'></div>"
    html += "</div>"

    st.markdown("### Timeline")
    st.markdown(html, unsafe_allow_html=True)

    # --- Export Timeline as ZIP ---
    def create_timeline_image(photo_dates, width=4000, height=600):
        if not photo_dates:
            return None
        min_date = min([x["date"] for x in photo_dates])
        max_date = max([x["date"] for x in photo_dates])
        total_days = (max_date - min_date).days or 1
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        y = height // 2
        # Draw timeline line
        draw.line((50, y, width-50, y), fill="black", width=3)
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()
        # Place each photo
        for pd in photo_dates:
            days_from_start = (pd["date"] - min_date).days
            x = 50 + int((width-100) * days_from_start / total_days)
            # Paste photo (resize to 80x80)
            try:
                photo = Image.open(io.BytesIO(pd["file_dict"]["bytes"])).resize((80, 80))
                img.paste(photo, (x-40, y-90))
            except Exception:
                pass
            # Draw label vertically with more margin and width
            label = pd["display"]
            label_img = Image.new("RGBA", (30, 140), (255, 255, 255, 0))
            label_draw = ImageDraw.Draw(label_img)
            label_draw.text((15, 0), label, fill="black", font=font, anchor="ma")
            label_img = label_img.rotate(90, expand=1)
            img.paste(label_img, (x-15, y+110), label_img)
        return img

    def export_timeline_zip(photo_dates):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            csv_rows = [("filename", "date")]
            label_counts = {}
            for pd in photo_dates:
                file_dict = pd["file_dict"]
                date = pd["date"]
                # Use robust filename logic
                if not pd["month_specified"]:
                    base = f"{date.year}"
                elif pd["month_specified"] and not pd["day_specified"]:
                    base = f"{date.year}-{pd['month']:02d}"
                else:
                    base = f"{date.year}-{pd['month']:02d}-{pd['day']:02d}"
                # Ensure unique filename
                count = label_counts.get(base, 0) + 1
                label_counts[base] = count
                if count == 1:
                    filename = f"{base}.jpg"
                else:
                    filename = f"{base}_{count}.jpg"
                zf.writestr(filename, file_dict["bytes"])
                # For CSV, use the label as above
                label = base
                csv_rows.append((filename, label))
            # Add CSV
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerows(csv_rows)
            zf.writestr("timeline.csv", csv_buffer.getvalue())
            # Add PNG timeline image
            timeline_img = create_timeline_image(photo_dates)
            if timeline_img:
                png_buf = io.BytesIO()
                timeline_img.save(png_buf, format="PNG")
                png_buf.seek(0)
                zf.writestr("timeline.png", png_buf.getvalue())
        zip_buffer.seek(0)
        return zip_buffer

    if st.button("Export Timeline as ZIP"):
        zip_buffer = export_timeline_zip(photo_dates)
        st.download_button(
            label="Download Timeline ZIP",
            data=zip_buffer,
            file_name="timeline_export.zip",
            mime="application/zip"
        )

    # --- 2. Send images to backend for processing ---
    with st.spinner("Uploading and processing images..."):
        files = [("files", (f["name"], f["bytes"], f["type"])) for f in photo_files]
        try:
            resp = requests.post(f"{BACKEND_URL}/upload-images/", files=files)
            if resp.status_code == 200:
                st.success("Images uploaded and processed!")
            else:
                st.warning(f"Backend error: {resp.text}")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")

    # --- 3. Fetch processed images from backend ---
    try:
        resp = requests.get(f"{BACKEND_URL}/processed-images/")
        processed_names = resp.json().get("images", [])
    except Exception as e:
        st.error(f"Could not fetch processed images: {e}")
        processed_names = []

    # --- 4. Estimate age for each image (placeholder logic) ---
    # In a real app, call an age estimation model here
    def fake_age_estimation(name):
        # Try to extract a number from the filename, else random
        import re
        match = re.search(r'(\d{4})', name)
        if match:
            return int(match.group(1)) - 1980  # crude guess
        return random.randint(5, 70)

    timeline = []
    for name in processed_names:
        age = fake_age_estimation(name)
        timeline.append({"name": name, "age": age})
    # Sort by age
    timeline.sort(key=lambda x: x["age"])

    # --- 5. Timeline UI ---
    if timeline:
        ages = [t["age"] for t in timeline]
        min_age, max_age = min(ages), max(ages)
        idx = st.slider(
            "Scroll through ages", 0, len(timeline)-1, 0,
            format="Age %d"
        )
        selected = timeline[idx]

        # --- 6. Show dynamic headshot ---
        st.subheader(f"Dynamic Headshot (Age {selected['age']})")
        img_url = f"{BACKEND_URL}/image/{selected['name']}"
        try:
            img_resp = requests.get(img_url)
            img = Image.open(io.BytesIO(img_resp.content))
            st.image(img, width=300)
        except Exception as e:
            st.warning(f"Could not load image: {e}")

        # --- 7. Show timeline as thumbnails ---
        st.markdown("### Timeline")
        cols = st.columns(len(timeline))
        for i, t in enumerate(timeline):
            with cols[i]:
                img_url = f"{BACKEND_URL}/image/{t['name']}"
                try:
                    img_resp = requests.get(img_url)
                    img = Image.open(io.BytesIO(img_resp.content))
                    st.image(img, width=80)
                    st.caption(f"Age {t['age']}")
                except:
                    st.write("(no image)")
else:
    st.info("Upload some images to get started!")

# --- Import Timeline ZIP ---
if not st.session_state.get("zip_imported"):
    imported_zip = st.file_uploader("Import Timeline ZIP (to restore timeline)", type=["zip"], key="import_zip")
    if imported_zip is not None:
        with zipfile.ZipFile(imported_zip) as zf:
            if "timeline.csv" not in zf.namelist():
                st.error("timeline.csv not found in ZIP. Please upload a valid exported timeline ZIP.")
            else:
                csv_file = zf.open("timeline.csv")
                reader = csv.reader(io.TextIOWrapper(csv_file))
                rows = list(reader)
                if len(rows) < 2:
                    st.error("timeline.csv is empty or invalid.")
                else:
                    # Clear current session state
                    st.session_state.photo_files = []
                    for filename, label in rows[1:]:
                        if filename not in zf.namelist():
                            continue
                        img_bytes = zf.read(filename)
                        # Parse label for year/month/day, handling padded hyphens
                        parts = label.split("-")
                        year = int(parts[0])
                        month = int(parts[1]) if len(parts) > 1 and parts[1] and parts[1] != "" else None
                        day = int(parts[2]) if len(parts) > 2 and parts[2] and parts[2] != "" else None
                        month_specified = month is not None
                        day_specified = day is not None
                        # Compose display string and flags
                        if not month_specified:
                            display_str = f"{year}--"
                        elif month_specified and not day_specified:
                            display_str = f"{year}-{int(month):02d}-"
                        else:
                            display_str = f"{year}-{int(month):02d}-{int(day):02d}"
                        # Compose date object (use 1 for missing month/day)
                        date = datetime.date(year, month if month else 1, day if day else 1)
                        st.session_state.photo_files.append({
                            "name": filename,
                            "bytes": img_bytes,
                            "type": "image/jpeg",
                            "imported": True,  # mark as imported
                            "date": date,
                            "display": display_str,
                            "month_specified": month_specified,
                            "day_specified": day_specified,
                            "year": year,
                            "month": month,
                            "day": day
                        })
                    st.success(f"Imported {len(st.session_state.photo_files)} images from timeline ZIP.")
                    st.session_state["zip_imported"] = True
                    st.rerun()
else:
    st.info("Timeline ZIP imported. To import another, reset uploads.") 