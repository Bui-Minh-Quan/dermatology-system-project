# Hệ thống hỗ trợ chẩn đoán và quản lý bệnh lý da liễu (Dermatology Support System)

## Thông tin sinh viên
* **Sinh viên thực hiện:** Bùi Minh Quân
* **Mã số sinh viên:** 23020415
* **Lớp:** K68-AI1
* **Đề tài:** Hệ thống đa phương thức hỗ trợ chẩn đoán và quản lý bệnh lý da liễu dựa trên Đồ thị tri thức (Knowledge Graph) và Học sâu (Deep Learning).

---

## Giới thiệu
Dự án tập trung vào việc cung cấp một công nghệ tiện lợi có thể sử dụng tại nhà để hỗ trợ chẩn đoán và quản lý bệnh lý da liễu. Hệ thống kết hợp sức mạnh của **Deep Learning** trong phân tích hình ảnh và **Knowledge Graph** để cung cấp khả năng tư vấn chuyên sâu, giúp tối ưu hóa quy trình làm việc giữa bệnh nhân và bác sĩ.

## Công nghệ sử dụng
* **Backend Framework:** FastAPI (Python 3.12+)
* **Hệ quản trị cơ sở dữ liệu:**
    * **PostgreSQL:** Lưu trữ dữ liệu quan hệ, thông tin người dùng và quản lý lịch hẹn.
    * **Neo4j:** Quản lý Đồ thị tri thức y khoa phục vụ công nghệ GraphRAG.
* **Trí tuệ nhân tạo:**
    * **Gemini 2.5 Flash:** Xử lý ngôn ngữ tự nhiên, trích xuất thực thể và tạo phản hồi.
    * **GraphRAG:** Truy vấn dữ liệu thực tế từ đồ thị tri thức để làm giàu ngữ cảnh tư vấn.
* **Hạ tầng:** Docker & Docker Compose.

## Các tính năng chính

### 1. Quản lý danh tính tập trung (Identity Management)
Lưu trữ thông tin bệnh nhân và bác sĩ.
* Bảng `User` lưu trữ thông tin định danh dùng chung (Họ tên, Ngày sinh, Giới tính, Avatar).
* Các bảng `Profile` riêng biệt lưu trữ dữ liệu chuyên môn đặc thù cho Bác sĩ và Bệnh nhân, giảm dữ liệu thừa.

### 2. Chẩn đoán đa phương thức (Multimodal Diagnosis)
API hỗ trợ tiếp nhận dữ liệu phức hợp bao gồm:
* Hình ảnh tổn thương da.
* Mô tả triệu chứng bằng văn bản.
* Vector vị trí cơ thể (Body Vector) để xác định ngữ cảnh lâm sàng.

Kết quả đầu ra:
* Chẩn đoán sơ bộ với độ tin cậy.
* Khoanh vùng tổn thương trên ảnh.
* Gợi ý các bước tiếp theo (Tư vấn, Đặt lịch khám).

### 3. Chatbot tư vấn y khoa (GraphRAG)
Sử dụng công nghệ RAG kết hợp với Neo4j để:
* Trích xuất thực thể y khoa từ câu hỏi của người dùng.
* Truy vấn mối quan hệ giữa các bệnh lý, triệu chứng và hoạt chất từ Knowledge Graph.
* Đưa ra lời khuyên cá nhân hóa dựa trên tiền sử bệnh lý và dị ứng của từng bệnh nhân.

### 4. Hệ thống đặt lịch hẹn khám 
Cho phép bệnh nhân đặt lịch hẹn khám với bác sĩ, đồng thời hệ thống sẽ tự động kiểm tra xung đột lịch trình của bác sĩ để đảm bảo tính khả dụng.

### 5. Gợi ý bác sĩ & Cơ sở y tế
Tự động đề xuất danh sách bác sĩ dựa trên việc phân tích chuyên khoa phù hợp với triệu chứng của người dùng, kết hợp sắp xếp theo điểm đánh giá và khoảng cách địa lý.

## 📂 Cấu trúc thư mục phần backend
```text
backend/
├── config/             # Cấu hình kết nối PostgreSQL, Neo4j
├── models/             # Định nghĩa Schema SQLAlchemy (User, Profile, Appointment...)
├── modules/            # Logic nghiệp vụ chính
|   |
|   |── ai_diagnosis/   # Xử lý chẩn đoán đa phương thức 
│   ├── auth/           # Đăng ký, đăng nhập, phân quyền JWT
│   ├── chatbot_rag/    # Xử lý NLP và truy vấn Knowledge Graph
│   ├── appointments/   # Quản lý đặt lịch và chống xung đột thời gian
│   └── profiles/       # Cập nhật thông tin định danh và y tế
|   └── recommendation/   # Gợi ý bác sĩ và cơ sở y tế
|   └── tracking/        # Theo dõi tiến trình điều trị và lịch sử bệnh án
├── initialization/     # Script khởi tạo dữ liệu (Seed Admin)
└── main.py             # Entry point của ứng dụng