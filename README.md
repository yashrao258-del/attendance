# 📸 Smart Face Attendance System

A real-time facial recognition attendance management system built with Flask and FaceNet. Automatically mark student attendance, detect late arrivals, and generate attendance reports.

## ✨ Features

- 🔐 **Secure Faculty Login** - Session-based authentication
- 📹 **Real-Time Face Recognition** - Live webcam-based attendance marking
- 🎯 **High Accuracy** - FaceNet embeddings with 0.90 distance threshold
- ⏰ **Late Detection** - Automatic late marking based on class start time
- 📊 **Attendance Reports** - View and download attendance as Excel files
- 👥 **Student Management** - Add/remove student faces dynamically
- 🎨 **Beautiful UI** - Responsive dashboard with Tailwind CSS

## 📋 Project Structure

ls -la README.md
cat > README.md << 'EOF'


A real-time facial recognition attendance management system built with Flask and FaceNet.

## 🚀 Quick Start

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running
```bash
source venv/bin/activate
python app.py
# Go to http://localhost:5001
# Login: faculty / faculty123
```

## 📋 Project Structure

- `app.py` - Flask backend
- `main.py` - Face recognition engine
- `add_face.py` - Student face capture
- `login.html` - Login page
- `index.html` - Dashboard

## 🔐 Default Login

Username: `faculty`  
Password: `faculty123`

## 📝 License

MIT License - Open source project
