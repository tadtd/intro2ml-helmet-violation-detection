# Báo Cáo Cuối Kỳ: Xây dựng và Triển khai Hệ thống Học máy Ứng dụng

## Cấu Trúc Báo Cáo

### Thông Tin Nhóm và Phân Công Công Việc
Liệt kê thành viên nhóm, MSSV, và mô tả ngắn gọn vai trò/đóng góp của từng người.

### Chương 1: Giới thiệu
- **Phân tích Vấn đề (Problem Definition):** Mô tả chi tiết bài toán, làm rõ tính cấp thiết và ý nghĩa trong bối cảnh thực tiễn Việt Nam.
- **Mục tiêu của Đồ án:** Trình bày các mục tiêu cụ thể.
- **Tổng quan về Phương pháp:** Mô tả ngắn gọn cách tiếp cận tổng thể, từ thu thập dữ liệu đến triển khai sản phẩm.

### Chương 2: Thu thập và Phân tích Dữ liệu
- **Nguồn và Phương pháp Thu thập:**
  - Trình bày nguồn dữ liệu (API, scraping, tự tạo,...).
  - Mô tả chi tiết quy trình và công cụ thu thập, định dạng lưu trữ.
- **Tiền xử lý và Làm sạch:** Mô tả các bước xử lý nhiễu, dữ liệu thiếu, chuẩn hóa, biến đổi.
- **Phân tích Khám phá Dữ liệu (EDA):**
  - Thống kê mô tả, phân tích phân bố nhãn, mối quan hệ giữa các thuộc tính.
  - Sử dụng biểu đồ, bảng minh họa phát hiện quan trọng.
  - Phân tích chất lượng dữ liệu và cách xử lý vấn đề (ngoại lệ, trùng lặp).

### Chương 3: Lựa chọn và Huấn luyện Mô hình
- **Chuẩn bị Dữ liệu cho Mô hình:**
  - Nêu rõ tỷ lệ chia Train/Validation/Test và lý do.
  - Tóm tắt các bước tiền xử lý cuối cùng.
- **Lựa chọn và Kiến trúc Mô hình:**
  - Trình bày, so sánh ít nhất 3 mô hình đã thử nghiệm.
  - Lý giải lý do lựa chọn; với Deep Learning cần vẽ sơ đồ và mô tả kiến trúc chi tiết.
- **Cấu hình Huấn luyện:**
  - Mô tả hàm mất mát, thuật toán tối ưu, siêu tham số chính.
  - Trình bày phương pháp tinh chỉnh tham số (Grid Search, Random Search,...).

### Chương 4: Kết quả và Thảo luận
- **Kết quả Thực nghiệm:**
  - Biểu đồ quá trình học (Learning Curves) trên Train/Validation, kèm nhận xét.
  - Chỉ số đánh giá (Accuracy, Precision, Recall, F1-Score, RMSE,...) trên tập Test.
  - Hiển thị và phân tích ma trận nhầm lẫn (Confusion Matrix).
- **So sánh và Thảo luận:**
  - Bảng so sánh hiệu năng giữa các mô hình.
  - Phân tích Overfitting/Underfitting và biện pháp đã áp dụng.
  - Phân tích các trường hợp dự đoán sai điển hình, đưa ra giả thuyết nguyên nhân.

### Chương 5: Xây dựng và Triển khai Ứng dụng
- **Kiến trúc Hệ thống:** Mô tả kiến trúc tổng thể, cách mô hình được đóng gói và tích hợp.
- **Giao diện và Chức năng:**
  - Mô tả UI và các chức năng chính.
  - Cung cấp hình ảnh chụp màn hình ứng dụng.
- **Triển khai:**
  - Nêu rõ nền tảng triển khai (cloud công khai hoặc local).
  - Nếu cloud công khai: cung cấp URL ứng dụng đang hoạt động.
  - Nếu local: cung cấp hướng dẫn cài đặt, câu lệnh chạy chi tiết.

### Chương 6: Kết luận
- **Tóm tắt Kết quả:** So với mục tiêu ban đầu.
- **Hạn chế:** Thẳng thắn chỉ ra hạn chế của mô hình và ứng dụng.
- **Hướng phát triển:** Đề xuất ý tưởng cải thiện/phát triển trong tương lai.

### Phụ lục
- **Tài liệu tham khảo:** Liệt kê các bài báo, sách, tài nguyên đã tham khảo.

---

## Yêu Cầu Về Trình Bày
1. **Văn phong:** Khoa học, khách quan, súc tích.
2. **Hình ảnh/Bảng biểu:** Mọi hình ảnh, bảng biểu phải được đánh số, có chú thích rõ ràng và được tham chiếu trong nội dung.
3. **Trích dẫn:** Trích dẫn đầy đủ nguồn tài liệu, kiến trúc mô hình tham khảo.
4. **Giới hạn:** Không vượt quá **30 trang** (không bao gồm phụ lục) và khoảng **7000 từ**.

## Các Sản Phẩm Phải Nộp
1. **Báo cáo Đồ án:** Tài liệu hoàn chỉnh theo cấu trúc trên.
2. **Mã nguồn:** Toàn bộ code (tiền xử lý, huấn luyện, ứng dụng web).
3. **Mô hình đã huấn luyện:** File trọng số của mô hình tốt nhất.
4. **Slide:** Slide trình bày cho buổi bảo vệ cuối kỳ.

**Tổ chức lưu trữ trên Cloud:** Tổ chức lưu trữ sản phẩm (mã nguồn, mô hình) trên nền tảng cloud (Google Drive, OneDrive,...).
- **Lưu ý:** Mã nguồn nên được quản lý trên GitHub/GitLab, cung cấp liên kết tới kho chứa công khai (public repository).

## Tiêu Chí Đánh Giá

| Mục | Trọng số | Đánh giá |
|---|---|---|
| Báo cáo Khoa học & Chiều sâu Lý thuyết | 30% | Phân tích vấn đề sắc bén. Trình bày cơ sở lý thuyết rõ ràng. Quy trình các bước đầy đủ, logic. Phân tích kết quả sâu sắc. |
| Sản phẩm Kỹ thuật (Code & Model) | 30% | Chất lượng code (sạch, hiệu quả, có chú thích). Mức độ đầu tư vào dữ liệu. Hiệu năng của mô hình cuối cùng so với các baseline. |
| Ứng dụng Web | 30% | Ứng dụng mô hình + tích hợp API hoạt động ổn định, giao diện thân thiện, giải quyết đúng bài toán. |
| Điểm Sáng tạo | 10% | Tạo ra sản phẩm đột phá và có giá trị thực tiễn cao. |