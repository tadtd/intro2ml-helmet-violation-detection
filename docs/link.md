Viewed docker-compose.yml:1-32

Sau khi bạn đã khởi chạy thành công cả Backend (bằng Docker) và Frontend (bằng lệnh `npm run dev`), dưới đây là các đường link (URL) để truy cập vào các service của hệ thống trên máy tính của bạn:

1. **Giao diện người dùng (Frontend - Next.js):**
   * 👉 **http://localhost:3000**
   * *(Đây là trang web chính để bạn xem dashboard và tương tác)*

2. **Máy chủ API (Backend - FastAPI):**
   * 👉 **http://localhost:8000** 
   * *(Đây là địa chỉ gốc của server xử lý logic)*

3. **Tài liệu API tự động (Swagger UI):**
   * 👉 **http://localhost:8000/docs**
   * *(Đây là trang vô cùng hữu ích do FastAPI tự tạo, giúp bạn xem danh sách tất cả các API đang có, cách chúng hoạt động và có thể test trực tiếp API tại đây).*

**Các Service chạy ngầm (Không có link giao diện web):**
* **Redis:** Chạy ở cổng `localhost:6379` (Dùng để làm Message Broker quản lý hàng đợi cho hệ thống).
* **Celery Worker:** Chạy ngầm trong Docker để xử lý các tác vụ nặng (như phân tích video, AI) mà không làm đứng API.
* **Cơ sở dữ liệu (Supabase):** Bạn truy cập thông qua trang chủ của Supabase (https://supabase.com/dashboard) theo tài khoản bạn đã đăng ký.