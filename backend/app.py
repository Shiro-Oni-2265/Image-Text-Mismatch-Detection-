import os
import uuid
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from configs.config import Config
from models.clip_model import ITMDCLIPModel
from inference.predict import predict

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

print("Loading model for API...")
device = torch.device(Config.DEVICE)
model = ITMDCLIPModel(Config.MODEL_NAME).to(device)
model.eval()

checkpoint_path = os.path.join(Config.OUTPUT_DIR, "best_model.pth")
checkpoint_loaded = False
if os.path.exists(checkpoint_path):
    try:
        model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        checkpoint_loaded = True
        print(f"Loaded tuned checkpoint from {checkpoint_path}")
    except Exception as e:
        print(f"Failed to load checkpoint: {e}. Using base CLIP.")

if not checkpoint_loaded:
    print("No checkpoint found — using base CLIP cosine similarity mode.")

UPLOAD_FOLDER = os.path.join(Config.DATA_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    if 'imageFile' not in request.files or 'caption' not in request.form:
        return jsonify({"error": "Missing imageFile or caption"}), 400

    file = request.files['imageFile']
    caption = request.form['caption'].strip()

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not caption:
        return jsonify({"error": "Caption cannot be empty"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Thread-safe filename using UUID
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Dùng autocast để inference nhanh hơn trên GPU
        use_amp = device.type == "cuda"
        if use_amp:
            import torch
            with torch.cuda.amp.autocast():
                sim_score, prediction_result = predict(
                    filepath, caption, model=model, checkpoint_loaded=checkpoint_loaded
                )
        else:
            sim_score, prediction_result = predict(
                filepath, caption, model=model, checkpoint_loaded=checkpoint_loaded
            )
        is_match = prediction_result == "MATCH"

        return jsonify({
            "isMatch": is_match,
            "simScore": round(sim_score, 4) if sim_score is not None else 0,
            "suggestedCaption": ""
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 16MB."}), 413

if __name__ == '__main__':
    app.run(debug=True, port=5000)
