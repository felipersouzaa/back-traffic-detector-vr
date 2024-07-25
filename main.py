import os
import asyncio
import aiohttp
import time
import cv2
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Cria uma instância da aplicação FastAPI
app = FastAPI()

# Variável de controle para pausar o download
is_paused = False

# Definição dos dados das câmeras
camera_data = [
    {"Id": 0, "Group": 0, "Address": "Camberwell New Rd/Brixton Rd", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04503.mp4", "Impacts": [2, 3]},
    {"Id": 1, "Group": 0, "Address": "A3 Clapham Rd/Elias Place", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04608.mp4", "Impacts": [3, 2]},
    {"Id": 2, "Group": 0, "Address": "Harleyford St/Ken Pk Rd", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04332.mp4", "Impacts": [-1]},
    {"Id": 3, "Group": 0, "Address": "Kenington Pk Rd/Kennington Oval", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04503.mp4", "Impacts": [-1]},
    {"Id": 4, "Group": 1, "Address": "Harleyford Rd/Vauxhall Grove", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04329.mp4", "Impacts": [5]},
    {"Id": 5, "Group": 1, "Address": "Kennington Lane", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.04300.mp4", "Impacts": [-1]},
    {"Id": 6, "Group": 2, "Address": "Parkhurst Rd by Holloway Rd", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.09605.mp4", "Impacts": [7]},
    {"Id": 7, "Group": 2, "Address": "Seven Sisters Rd/Holloway Rd", "Url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.09711.mp4", "Impacts": [-1]},
]

# Diretório para armazenar os vídeos
video_dir = "videos"
os.makedirs(video_dir, exist_ok=True)

# Diretório para armazenar os frames extraídos
frames_dir = "frames"
os.makedirs(frames_dir, exist_ok=True)

# Classe que define o modelo de dados da câmera
class Camera(BaseModel):
    Id: int
    Group: int
    Address: str
    Url: str
    Impacts: List[int]

# Classe que define o modelo de dados para informações das câmeras e dos frames extraídos
class CameraInfo(BaseModel):
    Camera1: Camera
    Camera2: Camera
    FramePath1: str
    FramePath2: str

# Função assíncrona para fazer o download de um vídeo
async def download_video(session, url, filepath):
    async with session.get(url) as response:
        with open(filepath, 'wb') as f:
            f.write(await response.read())

# Função assíncrona para baixar os vídeos das câmeras periodicamente
async def download_videos():
    global is_paused
    while True:
        if not is_paused:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for camera in camera_data:
                    timestamp = int(time.time())
                    filename = f"{camera['Id']}_{timestamp}.mp4"
                    filepath = os.path.join(video_dir, filename)
                    tasks.append(download_video(session, camera["Url"], filepath))
                await asyncio.gather(*tasks)
        await asyncio.sleep(10)  # Espera 10 segundos antes de baixar os próximos vídeos

# Evento de inicialização do aplicativo que inicia o download dos vídeos
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(download_videos())

# Rota para pausar o download de vídeos
@app.get("/pause_download")
def pause_download():
    global is_paused
    is_paused = True
    return {"status": "paused"}

# Rota para resumir o download de vídeos
@app.get("/resume_download")
def resume_download():
    global is_paused
    is_paused = False
    return {"status": "resumed"}

# Rota para obter a lista de câmeras
@app.get("/cameras", response_model=List[Camera])
def get_cameras():
    return camera_data

# Função para extrair um frame de um vídeo no timestamp especificado
def extract_frame(video_path: str, timestamp: float, frame_path: str):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second
    frame_number = int(fps * timestamp)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise ValueError(f"Could not extract frame at timestamp {timestamp}")
    cv2.imwrite(frame_path, frame)
    cap.release()

# Rota para obter as informações de um par de câmeras e extrair frames dos vídeos mais recentes
@app.get("/camera_pair/{camera_pair_id}", response_model=CameraInfo)
def get_camera_pair(camera_pair_id: int, timestamp: float = Query(...)):
    # Exemplo: id par 0 retorna câmera 0 e 1, par 1 retorna câmera 2 e 3, etc.
    camera1 = camera_data[camera_pair_id * 2]
    camera2 = camera_data[camera_pair_id * 2 + 1]
    
    video_path1 = max((os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.startswith(f"{camera1['Id']}_")), key=os.path.getctime, default=None)
    video_path2 = max((os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.startswith(f"{camera2['Id']}_")), key=os.path.getctime, default=None)

    if not video_path1 or not video_path2:
        raise HTTPException(status_code=404, detail="Video files not found for the specified camera pair")

    frame_path1 = os.path.join(frames_dir, f"{camera1['Id']}_{timestamp}.jpg")
    frame_path2 = os.path.join(frames_dir, f"{camera2['Id']}_{timestamp}.jpg")

    try:
        extract_frame(video_path1, timestamp, frame_path1)
        extract_frame(video_path2, timestamp, frame_path2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "Camera1": camera1,
        "Camera2": camera2,
        "FramePath1": frame_path1,
        "FramePath2": frame_path2
    }

# Iniciar o servidor FastAPI com Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
