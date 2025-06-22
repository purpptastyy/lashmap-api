from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
from rules import determine_eye_shape, get_mapping_recommendation, get_combined_recommendation
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import uuid

# Lade Supabase-Umgebungsvariablen
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hilfsfunktion zur Berechnung von Merkmalen für linkes/rechtes Auge
def get_eye_features(landmarks, side="left"):
    if side == "left":
        top = landmarks[159]
        bottom = landmarks[145]
        inner = landmarks[133]
        outer = landmarks[33]
    else:  # right eye
        top = landmarks[386]
        bottom = landmarks[374]
        inner = landmarks[362]
        outer = landmarks[263]

    eye_height = abs(top.y - bottom.y)
    eye_width = abs(outer.x - inner.x)
    open_ratio = eye_height / eye_width if eye_width != 0 else 0
    tilt_angle = outer.y - inner.y

    return open_ratio, tilt_angle

@app.post("/analyze-eye")
async def analyze_eye(image: UploadFile = File(...)):
    try:
        contents = await image.read()
        npimg = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as face_mesh:
            results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if not results.multi_face_landmarks:
                return JSONResponse(status_code=400, content={"error": "No face detected"})

            landmarks = results.multi_face_landmarks[0].landmark
            open_ratio, tilt_angle = get_eye_features(landmarks)

            eye_shape = determine_eye_shape(open_ratio, tilt_angle)
            recommendation = get_mapping_recommendation(eye_shape)

            return {
                "eye_shape": eye_shape,
                "open_ratio": round(open_ratio, 4),
                "tilt_angle": round(tilt_angle, 4),
                **recommendation
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analyze-both-eyes")
async def analyze_both_eyes(image: UploadFile = File(...)):
    try:
        # 1. Bilddaten lesen
        contents = await image.read()
        npimg = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        # 2. Gesichtsanalyse
        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as face_mesh:
            results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if not results.multi_face_landmarks:
                return JSONResponse(status_code=400, content={"error": "No face detected"})

            landmarks = results.multi_face_landmarks[0].landmark
            left_open, left_tilt = get_eye_features(landmarks, side="left")
            right_open, right_tilt = get_eye_features(landmarks, side="right")
            left_shape = determine_eye_shape(left_open, left_tilt)
            right_shape = determine_eye_shape(right_open, right_tilt)
            full_recommendation = get_combined_recommendation(left_shape, right_shape)

        # 3. Bild in Supabase Storage hochladen
        filename = f"{uuid.uuid4()}.jpg"
        bucket_name = "uploads"  # Achte auf korrekten Bucketnamen!
        # Bild in Storage hochladen
        res = supabase.storage.from_(bucket_name).upload(filename, contents, {"content-type": "image/jpeg"})
        # Public URL erzeugen
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"

        # 4. Logging in DB (mit Bild-URL)
        log_data = {
            "user_id": None,
            "image_url": public_url,
            "left_eye": {"shape": left_shape, "open_ratio": left_open, "tilt_angle": left_tilt},
            "right_eye": {"shape": right_shape, "open_ratio": right_open, "tilt_angle": right_tilt},
            "combined": full_recommendation,
            "raw_metrics": {
                "left_open": left_open, "right_open": right_open,
                "left_tilt": left_tilt, "right_tilt": right_tilt
            },
            "notes": None
        }
        supabase.table("lashmap_logs").insert(log_data).execute()

        # 5. Response an Client
        return {
            "image_url": public_url,
            "left_eye_shape": left_shape,
            "right_eye_shape": right_shape,
            "left_open_ratio": round(left_open, 4),
            "right_open_ratio": round(right_open, 4),
            "left_tilt_angle": round(left_tilt, 4),
            "right_tilt_angle": round(right_tilt, 4),
            **full_recommendation
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
