import os
import threading
import webbrowser
import socket
import logging
from flask import Flask, request, send_from_directory, jsonify, render_template_string, abort
from werkzeug.utils import secure_filename
from tkinter import Tk, Button, Label
import mimetypes

# -------------------------------
# Configuration
# -------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, 'uploads')
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx',
    'ppt', 'pptx', 'zip', 'rar', '7z', 'mp4', 'mp3', 'wav', 'mov', 'avi'
}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------
# Flask App Setup
# -------------------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Disable Flask logs in production
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'

# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def index():
    try:
        files = []
        for f in os.listdir(app.config['UPLOAD_FOLDER']):
            path = os.path.join(app.config['UPLOAD_FOLDER'], f)
            if os.path.isfile(path):
                mime, _ = mimetypes.guess_type(path)
                files.append({
                    'name': f,
                    'size': os.path.getsize(path),
                    'mime': mime or 'application/octet-stream'
                })
        files.sort(key=lambda x: x['name'].lower())
    except Exception:
        files = []

    server_ip = get_local_ip()
    server_port = 5000
    return render_template_string(INDEX_HTML, files=files, server_ip=server_ip, server_port=server_port)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify(success=False, message="No files provided"), 400

    files = request.files.getlist('files')
    saved_files = []

    for file in files:
        if file.filename == '':
            continue
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Avoid overwriting by appending number if exists
            counter = 1
            original_name = filename
            while os.path.exists(filepath):
                name, ext = os.path.splitext(original_name)
                filename = f"{name}({counter}){ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                counter += 1

            try:
                file.save(filepath)
                saved_files.append(filename)
            except Exception as e:
                app.logger.error(f"Failed to save {filename}: {e}")
                continue
        else:
            return jsonify(success=False, message=f"File type not allowed: {file.filename}"), 400

    if saved_files:
        return jsonify(success=True, uploaded=saved_files)
    else:
        return jsonify(success=False, message="No valid files uploaded"), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    except FileNotFoundError:
        abort(404)

@app.errorhandler(413)
def too_large(e):
    return jsonify(success=False, message="File too large. Max size: 100 MB."), 413

# -------------------------------
# Professional Frontend (Bootstrap 5 + Custom)
# -------------------------------
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="author" content="Niranga">
    <meta name="description" content="Local file sharing server for CIS students at SUSL">
    <title>2N Share</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📤</text></svg>">
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3f37c9;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
        }
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
            min-height: 100vh;
            padding-bottom: 80px;
        }
        .navbar-brand {
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .upload-area {
            border: 2px dashed #adb5bd;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            background: rgba(255,255,255,0.6);
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: var(--primary);
            background: rgba(67, 97, 238, 0.05);
        }
        .file-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            color: var(--primary);
        }
        .file-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .file-icon-sm {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #e9ecef;
            border-radius: 8px;
            margin-right: 15px;
            font-size: 1.2rem;
        }
        .file-info {
            flex: 1;
            text-align: left;
        }
        .file-name {
            font-weight: 500;
            color: var(--dark);
            text-decoration: none;
        }
        .file-name:hover {
            color: var(--primary);
        }
        .file-size {
            font-size: 0.85rem;
            color: #6c757d;
        }
        .btn-upload {
            background: var(--primary);
            border: none;
            padding: 10px 24px;
            font-weight: 600;
        }
        .btn-upload:hover {
            background: var(--secondary);
        }
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            background: var(--dark);
            color: white;
            padding: 10px 0;
            text-align: right;
            font-size: 0.9rem;
        }
        .loading {
            display: none;
            color: var(--primary);
            font-style: italic;
        }
        @media (max-width: 768px) {
            .container {
                padding: 0 15px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">2N Share</a>
            <span class="text-white-50 ms-2">Local File Sharing</span>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="alert alert-info text-center">
            <strong>Server Address:</strong> <code>{{ server_ip }}:{{ server_port }}</code>
            <br>
            <small class="text-muted">Share this address with others on your network to send/receive files.</small>
        </div>

        <!-- Upload Section -->
        <div class="card shadow-sm mb-4">
            <div class="card-body">
                <h5 class="card-title mb-3">📤 Upload Files</h5>
                <div id="dropZone" class="upload-area">
                    <div class="file-icon">📁</div>
                    <p><strong>Drag & drop files here</strong> or click to browse</p>
                    <p class="text-muted small">Max 100 MB per file • Supports images, docs, videos, archives</p>
                    <input type="file" id="fileInput" multiple style="display:none;">
                </div>
                <button id="uploadBtn" class="btn btn-upload mt-3 w-100">Upload Selected Files</button>
                <div id="loading" class="loading mt-2">Uploading... Please wait.</div>
            </div>
        </div>

        <!-- File List -->
        <div class="card shadow-sm">
            <div class="card-header bg-white">
                <h5 class="mb-0">📁 Uploaded Files ({{ files|length }})</h5>
            </div>
            <div class="file-list list-group list-group-flush">
                {% if files %}
                    {% for file in files %}
                    <div class="file-item">
                        <div class="file-icon-sm">
                            {% if file.mime.startswith('image/') %}
                                🖼️
                            {% elif file.mime.startswith('video/') %}
                                🎥
                            {% elif file.mime.startswith('audio/') %}
                                🔊
                            {% elif 'pdf' in file.mime %}
                                📄
                            {% elif 'zip' in file.mime or 'rar' in file.mime %}
                                📦
                            {% elif 'word' in file.mime or 'document' in file.mime %}
                                📝
                            {% else %}
                                📁
                            {% endif %}
                        </div>
                        <div class="file-info">
                            <a href="{{ url_for('uploaded_file', filename=file.name) }}" class="file-name" target="_blank">{{ file.name }}</a>
                            <div class="file-size">{{ "%.1f"|format(file.size / 1024) }} KB</div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="list-group-item text-center text-muted py-4">
                        No files uploaded yet.
                    </div>
                {% endif %}
            </div>
        </div>
    </div>

    <footer class="footer">
        <div class="container">
            <a href="https://www.linkedin.com/in/niranga-nayanajith-548a0a302/" target="_blank" class="text-white text-decoration-none">
                © 2N Technologies
            </a>
        </div>
    </footer>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const loading = document.getElementById('loading');

        // Open file dialog on drop zone click
        dropZone.addEventListener('click', () => fileInput.click());

        // Handle file selection
        fileInput.addEventListener('change', handleFiles);
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFiles();
            }
        });
                                    
        function handleFiles() {
            const files = fileInput.files;
            if (files.length === 0) return;
            dropZone.querySelector('p').innerHTML = `${files.length} file(s) selected`;
        }

        uploadBtn.addEventListener('click', async () => {
            const files = fileInput.files;
            if (files.length === 0) {
                alert('Please select files to upload.');
                return;
            }

            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }

            loading.style.display = 'block';
            uploadBtn.disabled = true;

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (result.success) {
                    location.reload();
                } else {
                    alert('Upload failed: ' + (result.message || 'Unknown error'));
                }
            } catch (error) {
                console.error('Upload error:', error);
                alert('Network error during upload. Check console for details.');
            } finally {
                loading.style.display = 'none';
                uploadBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
'''

# -------------------------------
# Server & GUI
# -------------------------------
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start_server():
    threading.Thread(target=run_flask, daemon=True).start()
    webbrowser.open("http://127.0.0.1:5000")

def create_gui():
    root = Tk()
    root.title("2N Share")
    root.geometry("300x200")
    root.resizable(False, False)

    Label(root, text="2N Share", font=("Helvetica", 20, "bold")).pack(pady=15)
    Button(root, text="🚀 Start Server", command=start_server, font=("Arial", 12), width=20).pack(pady=8)
    Button(root, text="🌐 Open Web Interface", command=lambda: webbrowser.open("http://127.0.0.1:5000"), font=("Arial", 12), width=20).pack(pady=8)
    Button(root, text="❌ Exit", command=root.quit, font=("Arial", 12), width=20).pack(pady=15)

    root.mainloop()

if __name__ == '__main__':
    create_gui()