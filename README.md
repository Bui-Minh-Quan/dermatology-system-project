# Hệ thống đa phương thức hỗ trợ chẩn đoán và quản lý bệnh lý da liễu dựa trên đồ thị tri thức và học sâu

## Thông tin Sinh viên thực hiện
* **Họ và tên:** Bùi Minh Quân
* **Mã số sinh viên:** 23020415
* **Lớp:** K68-AI1
* **Đề tài:** Hệ thống đa phương thức hỗ trợ chẩn đoán và quản lý bệnh lý da liễu dựa trên Đồ thị tri thức và Học sâu.

---

## Giới thiệu Dự án
Dự án tập trung xây dựng một nền tảng hỗ trợ y tế thông minh chuyên sâu về lĩnh vực da liễu, hỗ trợ đắc lực cho người dùng trong việc tự theo dõi và sàng lọc sức khỏe tại nhà. 

Hệ thống tích hợp hai cốt lõi công nghệ tiên tiến:
1. **Chẩn đoán đa phương thức (Multimodal Diagnosis):** Kết hợp đồng thời dữ liệu hình ảnh thương tổn da (Computer Vision), thông tin vị trí giải phẫu (Metadata dạng Vector nhị phân) và văn bản mô tả triệu chứng từ bệnh nhân (Natural Language Processing).
2. **Trợ lý y khoa thông minh (AI Chatbot RAG):** Sử dụng kiến trúc thế hệ mới kết hợp giữa Đồ thị tri thức (Knowledge Graph) và cơ chế RAG (Retrieval-Augmented Generation) giúp chatbot trả lời chính xác, đáng tin cậy dựa trên nguồn tri thức y khoa đã được kiểm chứng, giảm thiểu hiện tượng ảo tưởng (hallucination) của mô hình ngôn ngữ lớn.

*Định hướng tương lai:* Phát triển phân hệ điều phối để tối ưu hóa quy trình làm việc và tương tác từ xa giữa bệnh nhân và bác sĩ chuyên khoa da liễu.

---

## Kiến trúc Công nghệ

### 1. Backend Core Service
* **Framework:** FastAPI (Python 3.12) - Tối ưu hóa hiệu năng, xử lý bất đồng bộ (Async/Await) và tự động sinh tài liệu API (Swagger UI).
* **Database Management System:** * **PostgreSQL:** Lưu trữ dữ liệu quan hệ (Thông tin tài khoản, hồ sơ bệnh nhân, lịch sử chẩn đoán, v.v.).
  * **Neo4j / Vector Database:** Lưu trữ hệ thống thực thể, quan hệ và vector nhúng phục vụ kiến trúc Graph-RAG.
* **Migration Tool:** Alembic (Quản lý các phiên bản cấu trúc cơ sở dữ liệu).

### 2. AI Inference Service
* **Framework:** FastAPI độc lập, phục vụ chuyên biệt cho các tác vụ tính toán nặng và chạy mô hình học sâu.
* **Deep Learning Framework:** PyTorch.
* **Mô hình AI tích hợp:**
  * **Gatekeeper (Phễu lọc đầu vào):** Mô hình nhị phân xác định và phân loại ảnh có chứa vùng da hay không trước khi đưa vào phân tích chuyên sâu.
  * **Disease Classifier:** Phân loại các nhóm bệnh lý da liễu chủ đạo dựa trên đặc trưng hình ảnh kết hợp dữ liệu tab (Metadata vị trí).
  * **Text Tokenizer:** `vinai/phobert-base-v2` phục vụ xử lý tiếng Việt chuyên sâu cho văn bản triệu chứng.
  * **Xử lý trực quan trực quan hóa:** Grad-CAM tạo bản đồ nhiệt (Heatmap Overlay) hỗ trợ bác sĩ xác định vùng mô hình AI tập trung phân tích.
  * **RAG Pipeline:** Kết hợp truy vấn tri thức từ Graph Database và cơ sở dữ liệu Vector để sinh phản hồi tự nhiên bằng mô hình ngôn ngữ lớn Qwen.

### 3. Frontend App
* **Công nghệ nền tảng:** React (JavaScript)
* **Giao tiếp API:** Axios client tích hợp Interceptor tự động xử lý JWT Authentication.

### 4. Hạ tầng & Triển khai
* **Containerization:** Docker & Docker-compose giúp đóng gói độc lập Frontend, Backend và AI Inference Service thành các container riêng biệt, triển khai trên mọi môi trường một cách nhất quán.

---

## Các Tính năng Chính Hiện tại
* **Hệ thống Xác thực (Auth):** Đăng ký/Đăng nhập phân quyền rõ ràng giữa Bệnh nhân (Patient) và Bác sĩ (Doctor). Cơ chế cấp Token dạng JWT an toàn.
* **Chẩn đoán Da liễu AI:** Người dùng tải ảnh thương tổn, chọn vị trí xuất hiện triệu chứng qua giao diện nút bấm (tự động chuyển đổi thành Vector nhị phân 8 chiều) và nhập văn bản mô tả. Hệ thống trả về kết quả dự đoán kèm độ tin cậy và bản đồ nhiệt (Grad-CAM) trực quan hóa cạnh ảnh gốc.
* **Chatbot RAG:** Hỗ trợ tư vấn chuyên sâu, tự động lưu và hiển thị lịch sử trò chuyện theo từng phiên làm việc của người dùng.

---

## Lộ trình Phát triển Tính năng
* **Module Appointments:** Hệ thống đặt lịch hẹn khám bệnh trực tuyến với bác sĩ chuyên khoa.
* **Module Recommendation:** Thuật toán gợi ý bác sĩ và cơ sở y tế chuyên khoa da liễu phù hợp nhất dựa trên vị trí địa lý và tình trạng bệnh lý của bệnh nhân sau chẩn đoán.
* **Module Tracking:** Nhật ký theo dõi tiến triển của thương tổn da qua thời gian bằng hình ảnh.

---

## 📂 Cấu trúc Thư mục Dự án

```text
.
├── docker-compose.yml              # Quản lý orchestration cho toàn bộ hệ thống
├── backend/                         # Source code của dịch vụ Backend chính
│   ├── main.py                     # File khởi chạy FastAPI ứng dụng chính
│   ├── config/                     # Cấu hình hệ thống và kết nối Database
│   ├── alembic/                    # Database migration scripts
│   ├── models/                     # Định nghĩa ORM Models (Users, ChatMessages, v.v.)
│   ├── modules/                    # Chia module nghiệp vụ (auth, ai_diagnosis, chatbot_rag...)
│   └── static/                     # Lưu trữ file tĩnh (uploads ảnh gốc, heatmaps chẩn đoán)
├── ai-inference-service/           # Source code dịch vụ xử lý AI độc lập
│   ├── main.py                     # File khởi chạy dịch vụ AI
│   ├── weights/                    # Lưu trữ trọng số mô hình (.pth, .pt)
│   ├── models/                     # Kiến trúc mạng học sâu
│   └── services/                   # Logic xử lý inference, Grad-CAM và RAG pipeline
└── frontend/                        # Ứng dụng giao diện người dùng
    ├── src/
    │   ├── api.js                  # Axios client cấu hình sẵn JWT Interceptor
    │   ├── App.jsx                 # Điều hướng và phân luồng giao diện chính
    │   └── components/             # Các view thành phần (Auth, Diagnosis, Chatbot)
    └── vite.config.js              # Cấu hình đóng gói giao diện Vite
