from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import os
import subprocess
import pandas as pd
import sys
import glob
app = Flask(__name__)
app.secret_key = "faculty_super_secret_key"

KNOWN_FACES_DIR = "known_faces"
# ATTENDANCE_FILE is now dynamic per class

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple hardcoded check for faculty authentication
        if username == 'faculty' and password == 'faculty123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials. Please try again.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/start_attendance', methods=['POST'])
def start_attendance():
    data = request.json or {}
    class_name = data.get('class_name', 'General')
    class_time = data.get('class_time', '')
    try:
        # Pass class_name and class_time to main.py
        subprocess.Popen([sys.executable, "main.py", class_name, class_time])
        return jsonify({"status": "success", "message": f"Attendance system started for {class_name}."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/add_student', methods=['POST'])
def add_student():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"status": "error", "message": "Name is required."}), 400
    
    try:
        subprocess.Popen([sys.executable, "add_face.py", name])
        return jsonify({"status": "success", "message": f"Capture camera launched for {name}."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_students', methods=['GET'])
def get_students():
    try:
        if not os.path.exists(KNOWN_FACES_DIR):
            return jsonify({"students": []})
        students = sorted([os.path.splitext(f)[0] for f in os.listdir(KNOWN_FACES_DIR) if not f.startswith('.')])
        return jsonify({"students": students})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/remove_student', methods=['POST'])
def remove_student():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"status": "error", "message": "Name is required."}), 400
    
    file_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            # Try png fallback too just in case
        elif os.path.exists(os.path.join(KNOWN_FACES_DIR, f"{name}.png")):
            os.remove(os.path.join(KNOWN_FACES_DIR, f"{name}.png"))
        else:
            return jsonify({"status": "error", "message": "Student face file not found."}), 404
            
        return jsonify({"status": "success", "message": f"Student '{name}' removed successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_classes', methods=['GET'])
def get_classes():
    try:
        files = glob.glob("attendance_*.xlsx")
        classes = []
        for f in files:
            name = f.replace("attendance_", "").replace(".xlsx", "")
            classes.append(name)
        if not classes:
            classes = ["General"]
        return jsonify({"classes": sorted(classes)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_attendance', methods=['GET'])
def get_attendance():
    class_name = request.args.get('class_name', 'General')
    class_name = os.path.basename(class_name) # Sanitize
    attendance_file = f"attendance_{class_name}.xlsx"
    try:
        if not os.path.exists(attendance_file):
            return jsonify({"data": []})
        df = pd.read_excel(attendance_file, engine="openpyxl")
        df = df.fillna("")
        records = df.to_dict(orient='records')
        return jsonify({"data": records})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download_attendance', methods=['GET'])
def download_attendance():
    class_name = request.args.get('class_name', 'General')
    class_name = os.path.basename(class_name)
    attendance_file = f"attendance_{class_name}.xlsx"
    if os.path.exists(attendance_file):
        return send_file(attendance_file, as_attachment=True, download_name=f"{class_name}_Attendance.xlsx")
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
