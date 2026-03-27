

# 🚑 MedShield AI

### Real-Time Emergency Triage & Hospital Allocation System

---

## 📌 Overview

**MedShield AI** is an intelligent healthcare platform that uses AI to **analyze patient conditions, prioritize emergencies, and allocate the nearest suitable hospital in real-time**.

It aims to **reduce treatment delays, optimize hospital resources, and save lives** during critical situations.

---

## 🚀 Key Features

* 🧠 **AI-Powered Triage System**
  Predicts severity using patient symptoms & vitals

* 📍 **Smart Hospital Allocation**
  Finds nearest hospital with available beds & facilities

* 🚑 **Emergency Response Optimization**
  Reduces waiting & travel time

* 💸 **Government Scheme Integration**
  Suggests eligible schemes (Ayushman Bharat, etc.)

* 📊 **Real-Time Dashboard**
  Displays patient flow, hospital capacity, alerts

* 🔔 **Alert System**
  Emergency notifications for hospitals

---

## 🏗️ System Architecture

```
User Input → AI Model → Severity Prediction
                        ↓
               Hospital Matching Engine
                        ↓
              Best Hospital Allocation
                        ↓
         Scheme Recommendation + Dashboard
```

---

## 🛠️ Tech Stack

### 💻 Frontend

* React.js / Streamlit
* Tailwind CSS

### ⚙️ Backend

* Python (FastAPI / Flask)

### 🤖 AI/ML

* Scikit-learn / TensorFlow
* Naive Bayes / Logistic Regression

### 🗄️ Database

* MySQL / PostgreSQL

### ☁️ Deployment

* Docker
* AWS / Render / Railway

---

## 📂 Project Structure

```
MedShield-AI/
│
├── frontend/
├── backend/
├── models/
├── dataset/
├── api/
├── utils/
├── docker/
├── README.md
└── requirements.txt
```

---

## ⚡ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/MedShield-AI.git
cd MedShield-AI
```

---

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Run Backend

```bash
uvicorn main:app --reload
```

---

### 4️⃣ Run Frontend (Streamlit example)

```bash
streamlit run app.py
```

---

## 🤖 AI Model Details

* Input: Symptoms, vitals, patient data
* Output: Severity Level (Low / Medium / High / Critical)

### Algorithms Used:

* Naive Bayes
* Logistic Regression
* KNN (optional)

---

## 📊 Use Cases

* 🚑 Emergency ambulance routing
* 🏥 Smart hospital management
* 🌍 Rural healthcare optimization
* 🧑‍⚕️ Doctor decision support

---

## 🎯 Target Audience

* Hospitals
* Government health departments
* Ambulance services
* NGOs & healthcare startups

---

## 🌍 Impact

* ⏱️ Reduces emergency response time
* 💰 Minimizes treatment cost
* ❤️ Saves lives through faster decisions
* 📈 Improves healthcare efficiency

---

## 🔮 Future Enhancements

* 🧾 EHR (Electronic Health Records) integration
* 📱 Android/iOS mobile app
* 🌐 Real-time GPS ambulance tracking
* 🤖 Advanced deep learning models

---

