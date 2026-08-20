import os
from flask import Flask, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pdf2docx import Converter

# Initialize the elite Flask engine
app = Flask(__name__, static_folder='.', static_url_path='')

# Configure secure storage directories
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB safety limit

# 1. UI Route: Serve your existing index.html
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Catch-all route to prevent 404 errors on refresh
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory('.', 'index.html')

# 2. Processing Route: Handle the heavy lifting
@app.route('/api/convert', methods=['POST'])
def convert_pdf():
    # Verify file existence
    if 'pdfFile' not in request.files:
        return jsonify({'error': 'Protocol Error: No PDF file provided.'}), 400
    
    file = request.files['pdfFile']
    if file.filename == '':
        return jsonify({'error': 'Protocol Error: Empty filename.'}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        # Secure the filename and save locally
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        # Define output destination
        output_filename = filename.rsplit('.', 1)[0] + '.docx'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        try:
            print(f"[PROCESSING] Analyzing layout for: {filename}")
            
            # THE ELITE ENGINE: Convert with layout, tables, and images preserved
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            return jsonify({
                'success': True,
                'message': 'Layout compilation successful.',
                'downloadUrl': f'/api/download/{output_filename}'
            })
            
        except Exception as e:
            print(f"[ERROR] Engine Failure: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to compile document architecture.'}), 500
            
        finally:
            # Clean up the input PDF to save server memory
            if os.path.exists(input_path):
                os.remove(input_path)
    
    return jsonify({'error': 'Invalid format. Engine only accepts .pdf'}), 400

# 3. Download Route: Transfer the final Word file back to the client
@app.route('/api/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'Requested document not found or expired.'}), 404

# Boot sequence
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 Python Conversion Engine Online on port {port}\n")
    app.run(host='0.0.0.0', port=port)
