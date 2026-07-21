## Cấu trúc slide đề xuất (~18 slide)

**1. Slide mở đầu**
- Tên đồ án, tên nhóm, giảng viên hướng dẫn (nếu có)

**2–3. Giới thiệu (Chương 1)**
- Bài toán là gì, vì sao cần thiết (bối cảnh Việt Nam)
- Mục tiêu cụ thể của đồ án
- Sơ đồ tổng quan pipeline (từ thu thập dữ liệu → mô hình → ứng dụng)

**4–6. Dữ liệu (Chương 2)**
- Nguồn dữ liệu & cách thu thập (API/scraping/tự tạo)
- Tiền xử lý: các bước làm sạch chính
- EDA: 1–2 biểu đồ nổi bật nhất (phân bố nhãn, tương quan thuộc tính…)

**7–10. Mô hình (Chương 3)**
- Cách chia tập Train/Val/Test
- Bảng so sánh ≥3 mô hình đã thử (tên mô hình – ưu/nhược điểm)
- Sơ đồ kiến trúc (nếu là Deep Learning)
- Cấu hình huấn luyện: loss, optimizer, siêu tham số chính, phương pháp tuning

**11–14. Kết quả (Chương 4)**
- Learning curves (Loss/Accuracy theo epoch)
- Bảng chỉ số đánh giá trên tập Test (Accuracy, Precision, Recall, F1…)
- Confusion matrix + nhận xét
- Bảng so sánh hiệu năng giữa các mô hình, phân tích overfitting/underfitting nếu có
- 1–2 ví dụ dự đoán sai điển hình + giả thuyết nguyên nhân

**15–17. Ứng dụng (Chương 5)**
- Sơ đồ kiến trúc hệ thống (model được đóng gói/tích hợp thế nào)
- Screenshot giao diện + demo (video ngắn hoặc link demo trực tiếp nếu deploy cloud)
- Nền tảng triển khai + link/cách chạy

**18. Kết luận (Chương 6)**
- Kết quả đạt được so với mục tiêu
- Hạn chế còn tồn tại
- Hướng phát triển tiếp theo

**19. Slide kết**
- Lời cảm ơn / Q&A