# Hệ thống Đa phương thức Chẩn đoán Bệnh Da liễu

**Thông tin sinh viên thực hiện:**
* **Họ và tên:** Bùi Minh Quân
* **Mã số sinh viên:** 23020415
* **Lớp:** K68-AI1

---

## 1. Mô tả dự án
Dermatology AI là một hệ thống y tế thông minh được thiết kế nhằm hỗ trợ chẩn đoán và tư vấn các bệnh lý da liễu phổ biến. Người dùng có thể thực hiện kiểm tra tình trạng da bằng cách tải lên hình ảnh chụp thương tổn, kèm theo văn bản mô tả triệu chứng và vị trí giải phẫu xuất hiện tổn thương (thông tin mô tả triệu chứng và vị trí là tùy chọn, không bắt buộc).

Hệ thống tập trung vào **9 nhóm bệnh da liễu có tần suất gặp cao** (bao gồm Mụn trứng cá, Viêm da cơ địa, Viêm da tiếp xúc, Vảy nến, Trứng cá đỏ, Viêm da tiết bã, Nấm da, Mề đay, và Da bình thường). Đây là các bệnh lý thường có biểu hiện lâm sàng tương tự nhau, do đó việc kết hợp đa nguồn dữ liệu (hình ảnh, văn bản và vị trí) giúp nâng cao độ chính xác trong chẩn đoán.

Bên cạnh chẩn đoán, hệ thống còn tích hợp một **Trợ lý AI Y khoa (Medical Chatbot)** sử dụng nguồn tri thức chuẩn xác để giải đáp thắc mắc, cung cấp kiến thức bệnh học, và gợi ý hướng điều trị/chăm sóc phù hợp cho người bệnh.

---

## 2. Tính năng hệ thống

* **Chẩn đoán đa phương thức (Multimodal Diagnosis):** Tích hợp phân tích đồng thời 3 luồng dữ liệu: Hình ảnh thương tổn da (Computer Vision), vector nhị phân 8 chiều chỉ định vị trí giải phẫu (Tabular Metadata), và văn bản mô tả triệu chứng (NLP). Kết quả trả về gồm tên bệnh dự đoán, độ tin cậy, và Bản đồ nhiệt (Grad-CAM++) trực quan hóa vùng tổn thương mà mô hình tập trung phân tích.
* **Trợ lý Y khoa Thông minh (Medical Chatbot):** Chatbot hỗ trợ hỏi đáp y tế dựa trên kiến trúc Hybrid Graph-RAG (kết hợp Vector Search và Knowledge Graph), giúp cung cấp thông tin điều trị, triệu chứng và thuốc dựa trên tài liệu y khoa chuẩn xác, hạn chế tình trạng ảo giác thông tin của LLM.
* **Xác thực & Quản trị tài khoản (Auth & Roles):** Hệ thống phân quyền chặt chẽ giữa Bệnh nhân (Patient) và Bác sĩ (Doctor), xác thực an toàn qua JSON Web Tokens (JWT).

---

## 3. Công nghệ sử dụng

* **Frontend:** React, Vite, Axios (tích hợp JWT Interceptor), HTML5/CSS3.
* **Backend:** FastAPI, SQLAlchemy (ORM), Alembic (Database Migration), Uvicorn.
* **AI & Machine Learning:**
  * *Deep Learning & Frameworks:* PyTorch, torchvision, transformers.
  * *Computer Vision:* MobileNetV3 (Gatekeeper lọc ảnh không chứa da), EfficientNetV2-S (Trích xuất đặc trưng ảnh), Grad-CAM++ (Sinh Heatmap giải thích mô hình).
  * *NLP & LLM Serving:* PhoBERT (`vinai/phobert-base-v2`), Ollama (triển khai Qwen 2.5 và `nomic-embed-text`), LangChain.
* **Databases & Vector Store:**
  * *PostgreSQL (với tiện ích mở rộng `pgvector`):* Quản lý dữ liệu người dùng, hồ sơ bệnh án và lưu trữ Vector Embeddings.
  * *Neo4j:* Quản lý Đồ thị tri thức y khoa (quan hệ Bệnh - Triệu chứng - Thuốc) phục vụ Graph-RAG.
* **DevOps & Hạ tầng:** Docker, Docker Compose.

---

## 4. Demo Hệ thống

* **Báo cáo chi tiết:** [Xem báo cáo tại Google Drive](https://drive.google.com/file/d/1Fa_Mp9NcVOGBRMnkYCHcAiaeJWsYyhLa/view?usp=drive_link).
* **Video Demo hoạt động:** [Xem video tại Google Drive](https://drive.google.com/file/d/1z7UpBKBKiAQ_uot77OKDmvhc5U5Ka6VC/view?usp=sharing)


---

## 5. Hướng dẫn cài đặt

### Yêu cầu tiên quyết
* Đã cài đặt [Docker](https://www.docker.com/) và Docker Compose.
* Đã cài đặt [Ollama](https://ollama.ai/) và kéo các mô hình cần thiết:
  ```bash
  ollama pull qwen2.5:1.5b
  ollama pull nomic-embed-text
  ```

### Các bước khởi chạy

**Bước 1: Khởi động cơ sở dữ liệu qua Docker Compose**
```bash
docker-compose up -d
```
*Lệnh này sẽ khởi chạy container PostgreSQL (pgvector) tại cổng `5432` và Neo4j tại cổng `7474`/`7687`.*

**Bước 2: Cài đặt và chạy Backend Core Service**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
pip install -r requirements.txt

# Chạy migration để khởi tạo cấu trúc cơ sở dữ liệu
alembic upgrade head

# Khởi chạy server FastAPI Backend (Cổng 8000)
uvicorn main:app --reload --port 8000
```

**Bước 3: Cài đặt và chạy AI Inference Service**
Mở một terminal mới:
```bash
cd ai-inference-service
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
pip install -r requirements.txt

# Nạp dữ liệu tri thức vào PostgreSQL và Neo4j (Chỉ chạy lần đầu)
python services/ingestion/vector_indexer.py
python services/ingestion/neo4j_indexer.py

# Khởi chạy AI Service (Cổng 8001)
uvicorn main:app --reload --port 8001
```

**Bước 4: Khởi chạy Frontend**
Mở một terminal mới:
```bash
cd frontend
npm install
npm run dev
```
Truy cập giao diện tại `http://localhost:5173` hoặc địa chỉ hiển thị trên terminal.

## 6. Cấu trúc dự án

```text
.
├── docker-compose.yml              # Cấu hình container cho PostgreSQL (pgvector) và Neo4j
├── backend/                        # Dịch vụ Backend quản lý nghiệp vụ và xác thực
│   ├── main.py                     # Entry point của Backend API
│   ├── config/                     # Cấu hình kết nối cơ sở dữ liệu
│   ├── alembic/                    # Quản lý Database Migrations
│   ├── models/                     # Định nghĩa Schema ORM (User, AIDiagnosis, ChatMessage...)
│   ├── modules/                    # Các module tính năng (auth, ai_diagnosis, chatbot_rag...)
│   └── static/                     # Lưu trữ file tải lên và ảnh heatmap
├── ai-inference-service/           # Microservice độc lập xử lý mô hình Deep Learning & RAG
│   ├── main.py                     # Entry point của AI Inference API
│   ├── models/                     # Định nghĩa kiến trúc mạng học sâu (Gatekeeper, Classifier)
│   ├── weights/                    # Chứa checkpoint trọng số mô hình (.pth, .pt)
│   └── services/                   
│       ├── diagnosis/              # Pipeline xử lý hình ảnh, nội suy và sinh Grad-CAM++
│       ├── ingestion/              # Script đọc dữ liệu, nạp vector và xây dựng đồ thị Neo4j
│       └── rag/                    # Pipeline truy vấn đa nguồn (Vector + Graph) và giao tiếp LLM
└── frontend/                       # Giao diện người dùng Web (React + Vite)
    ├── src/
    │   ├── api.js                  # Cấu hình Axios Client và JWT Interceptor
    │   ├── App.jsx                 # Điều hướng và hiển thị giao diện chính
    │   └── components/             # Các view thành phần (Auth, Diagnosis, Chatbot...)
    └── vite.config.js              # Cấu hình Vite
```
