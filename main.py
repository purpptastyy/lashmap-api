from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
from rules import determine_eye_shape, get_mapping_recommendation
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS aktivieren für Browsertests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hilfsfunktion zur Berechnung von Merkmalen
def get_eye_features(landmarks):
    # Landmark-IDs für rechtes Auge (MediaPipe)
    left_top = landmarks[159]
    left_bottom = landmarks[145]
    left_inner = landmarks[133]
    left_outer = landmarks[33]

    # Höhe und Breite berechnen
    eye_height = abs(left_top.y - left_bottom.y)
    eye_width = abs(left_outer.x - left_inner.x)
    open_ratio = eye_height / eye_width if eye_width != 0 else 0

    # Neigung berechnen (vertikaler Unterschied der X-Achse)
    tilt_angle = left_outer.y - left_inner.y

    return open_ratio, tilt_angle, {
        "left_top": (left_top.x, left_top.y),
        "left_bottom": (left_bottom.x, left_bottom.y),
        "left_inner": (left_inner.x, left_inner.y),
        "left_outer": (left_outer.x, left_outer.y),
    }

@app.post("/analyze-eye")
async def analyze_eye(image: UploadFile = File(...)):
    try:
        contents = await image.read()
        npimg = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        # MediaPipe Setup
        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as face_mesh:
            results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            if not results.multi_face_landmarks:
                return JSONResponse(status_code=400, content={"error": "No face detected"})

            landmarks = results.multi_face_landmarks[0].landmark
            open_ratio, tilt_angle, landmark_debug = get_eye_features(landmarks)

            eye_shape = determine_eye_shape(open_ratio, tilt_angle)
            recommendation = get_mapping_recommendation(eye_shape)

            return {
                "eye_shape": eye_shape,
                "open_ratio": round(open_ratio, 4),
                "tilt_angle": round(tilt_angle, 4),
                "landmark_points": landmark_debug,
                **recommendation
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
