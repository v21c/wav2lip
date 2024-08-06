from flask import Flask, request, jsonify, render_template, send_file
from pymongo import MongoClient
import gridfs
import os
from bson.objectid import ObjectId
from io import BytesIO
import requests

# Ngrok URL 설정 (Ngrok 실행 후 얻은 URL로 설정)
NGROK_URL = "https://your_ngrok_url.ngrok-free.app"

url = "https://api.synclabs.so/lipsync"

app = Flask(__name__)

# MongoDB Atlas 연결 설정
MONGO_URI = 'mongodb+srv://your_username:your_password@cluster0.your_cluster.mongodb.net/'
client = MongoClient(MONGO_URI)
db = client['your_database']
fs = gridfs.GridFS(db)

@app.route('/')
def index():
    results = list(db.results.find().sort("createdAt", -1))
    return render_template('index.html', results=results)

@app.route('/process', methods=['POST'])
def process():
    try:
        # MongoDB에서 비디오 및 오디오 데이터 가져오기
        video_data = db.testdata.find_one({'type': 'video'}, sort=[('_id', -1)])
        audio_data = db.testdata.find_one({'type': 'audio'}, sort=[('_id', -1)])
        
        if not video_data or not audio_data:
            return render_template('index.html', error='Video or audio not found')
        
        # Ngrok URL을 사용하여 외부에서 접근 가능한 파일 URL 생성
        video_url = f'{NGROK_URL}/file/{str(video_data["file_id"])}'  # ObjectId를 문자열로 변환
        audio_url = f'{NGROK_URL}/file/{str(audio_data["file_id"])}'  # ObjectId를 문자열로 변환
        api_key = 'your_api_key'

        # Wav2Lip API 요청 페이로드 준비
        payload = {
            'audioUrl': audio_url,
            'videoUrl': video_url,
            "maxCredits": 123,
            "model": "wav2lip++",
            "synergize": True,
            "pads": [0, 5, 0, 0],
            "synergizerStrength": 1,
            "webhookUrl": f"{NGROK_URL}/webhook"
        }
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print(f"Request Payload: {payload}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        if response.status_code == 200 or response.status_code == 201:
            return render_template('index.html', message="Lip sync processing started, waiting for completion.")
        else:
            error_message = response.json().get('message', 'Unknown error')
            print(f"Error Message: {error_message}")
            return render_template('index.html', error=f"Lip sync processing failed: {error_message}")
    except Exception as e:
        print(f"Exception: {str(e)}")
        return render_template('index.html', error=f"An error occurred: {str(e)}")

@app.route('/file/<file_id>')
def serve_file(file_id):
    try:
        file_id = ObjectId(file_id)
        file = fs.get(file_id)
        return send_file(BytesIO(file.read()), download_name=file.filename)
    except Exception as e:
        return str(e), 404

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if data:
        print(f"Webhook data received: {data}")
        result = data.get('result')
        error = data.get('error')
        if error:
            print(f"Error in lip sync processing: {error}")
        else:
            print(f"Lip sync completed successfully: {result}")
            # 결과를 데이터베이스에 저장
            db.results.insert_one(result)
        return jsonify({'status': 'received'}), 200
    else:
        print("No data received in webhook.")
        return jsonify({'status': 'no data'}), 400

if __name__ == '__main__':
    app.run(debug=True)
