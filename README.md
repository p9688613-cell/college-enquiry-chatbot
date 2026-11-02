# AI Chatbot for College Enquiries

A beginner-friendly, web-based AI/NLP Chatbot application designed to answer student queries regarding college admissions, courses, fees, exams, scholarships, hostels, library facilities, and contact information.

Built as a final-year Bachelor of Computer Applications (BCA) capstone project.

---

## 🌟 Key Features

1. **Interactive Chat Interface**: Clean, modern, responsive conversational UI accessible on laptops, desktops, and mobile devices.
2. **AI / NLP Intent Classification**: Uses Term Frequency - Inverse Document Frequency (TF-IDF) feature extraction with Cosine Similarity vector matching against pre-trained intent patterns.
3. **Pre-Loaded Knowledge Base**: 16+ college query categories including admissions, eligibility, courses, fees, scholarships, hostel, library, placements, and examinations.
4. **Clickable Follow-Up Suggestions**: Dynamic quick-action question buttons attached to bot responses.
5. **Intelligent Fallback Mechanism**: Gracefully handles out-of-scope or unknown questions with helpful guidance.
6. **Administrative Dashboard (`/admin`)**: Web portal to view analytics, add new FAQs, delete FAQs, view student query logs, and inspect unanswered questions.
7. **SQLite Database Integration**: Seamless storage and retrieval of frequently asked questions and student interaction logs.
8. **Interactive Voice Support**: Integrated browser-based Speech-to-Text (Voice Recognition) and Text-to-Speech (Audio response) using Web Speech APIs.
9. **Zero Paid APIs**: Completely free, open-source, and runs 100% locally on your machine without external cloud API dependencies.

---

## 📁 Project Folder Structure

```
college_enquiry_chatbot/
│
├── app.py                     # Flask server routes and API endpoints
├── chatbot.py                 # NLP intent classification and AI matching engine
├── database.py                # SQLite database helper module
├── requirements.txt           # Python dependencies
├── faqs.json                  # Initial seed FAQ data
├── README.md                  # Project documentation & setup instructions
├── college_chatbot.db         # Auto-generated SQLite database file
│
├── data/
│   └── intents.json           # NLP training patterns, responses & suggestions
│
├── templates/
│   ├── index.html             # Student chatbot web interface
│   └── admin.html             # Administrative FAQ and analytics portal
│
├── static/
│   ├── css/
│   │   └── style.css          # Modern CSS styling and animations
│   └── js/
│       └── script.js          # Client-side chat logic, voice input & fetch API
│
└── tests/
    └── test_chatbot.py        # Automated test suite (11 test cases)
```

---

## 🚀 Quick Start Guide (Windows)

### Step 1: Open Terminal in Project Folder
Open Visual Studio Code, press ``Ctrl + ` `` to open the integrated terminal, and ensure you are in the `college_enquiry_chatbot` directory:
```bash
cd college_enquiry_chatbot
```

### Step 2: Create and Activate Virtual Environment (Recommended)
```bash
python -m venv venv
.\venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Open in Web Browser
- Student Chatbot: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- Admin Portal: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)

---

## 🧪 Running Unit Tests

To run the automated test suite verifying greetings, admission questions, fee queries, unknown query fallbacks, and database operations:

```bash
python -m unittest tests/test_chatbot.py
```

---

## 🏫 How to Customize for Your Own College

1. **Change College Name & Branding**:
   - Open `templates/index.html` and edit lines 28–30 (e.g., change `Apex Institute of Technology` to your college name).
   - In `templates/admin.html`, update the header title.

2. **Update Contact Information & Fees**:
   - Open `data/intents.json`.
   - Search for `"tag": "contact"` and update the phone numbers, campus address, and email ID.
   - Search for `"tag": "fees"` and `"tag": "courses"` to adjust your college's specific degree programs and fee structure.

3. **Add New FAQs via Admin Dashboard**:
   - Start the app and navigate to `http://127.0.0.1:5000/admin`.
   - Fill out the **Add New FAQ** form with Category, Question, and Answer.
   - Click **Save FAQ to Database**. The chatbot will immediately be able to answer questions matching your new FAQ!

---

## 💻 System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 2 GB (4 GB recommended)
- **Disk Space**: 50 MB
- **Web Browser**: Google Chrome, Microsoft Edge, or Mozilla Firefox

