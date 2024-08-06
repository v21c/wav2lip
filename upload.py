import os
from pymongo import MongoClient
import gridfs

# MongoDB Atlas 연결 설정
MONGO_URI = 'mongodb+srv://your_username:your_password@cluster0.your_cluster.mongodb.net/'
client = MongoClient(MONGO_URI)
db = client['your_database']
fs = gridfs.GridFS(db)

def upload_file(file_path, file_type):
    with open(file_path, 'rb') as f:
        file_id = fs.put(f, filename=os.path.basename(file_path))
        db.testdata.insert_one({
            "type": file_type,
            "title": os.path.basename(file_path),
            "file_id": file_id
        })
        print(f"{file_type.capitalize()} file uploaded with ID: {file_id}")

# 비디오와 오디오 파일 경로 설정
video_file_path = r"C:\Users\your_username\Downloads\your_video_file.mp4"
audio_file_path = r"C:\Users\your_username\Downloads\your_audio_file.mp3"

# 파일 업로드
upload_file(video_file_path, 'video')
upload_file(audio_file_path, 'audio')
