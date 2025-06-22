from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
from rules import determine_eye_shape, get_mapping_recommendation, get_combined_recommendation
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hilfsfunktion zur Berechnung von Merkmalen
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
        contents = await image.read()
        npimg = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

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

            return {
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
