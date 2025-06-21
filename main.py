from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp

app = FastAPI()

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

            # --- Dummy Analysis (hier wird später Mapping etc. berechnet)
            response = {
                "eye_shape": "monolid",
                "mapping": "Cat Eye",
                "curl": "CC Curl",
                "length": "9–13 mm"
            }
            return response
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
