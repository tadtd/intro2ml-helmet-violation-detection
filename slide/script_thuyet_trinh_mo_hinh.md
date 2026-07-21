# Script thuyết trình — Phần "Mô hình" (lời văn tự nhiên)

> Bám 3 slide: **Các mô hình thử nghiệm → Kiến trúc & cơ chế → Cấu hình huấn luyện (Ray Tune)**.
> Phần **Script** viết theo lối nói, cứ đọc trôi như đang kể; phần *Giải thích sâu* để tự tin và trả lời khi bị hỏi.
> Thời lượng: **3–4 phút**. Phần đọc đã cắt gọn còn ý bắt buộc; chi tiết phụ nằm ở *Giải thích sâu* để phòng khi bị hỏi.

---

## Mở đầu

> "Phần trước là dữ liệu. Bây giờ em xin sang phần mô hình: vì sao nhóm em chọn ba mô hình này, bên trong chúng chạy ra sao, và nhóm em huấn luyện thế nào."

---

## SLIDE 1 — Vì sao ba mô hình

### Script

> "Nhóm em thử ba mô hình, và chúng không chọn ngẫu nhiên: mỗi cái đại diện một trường phái thiết kế, để so sánh cho công bằng.
>
> YOLO là trường phái một giai đoạn, nhẹ nhất với gần 22 triệu tham số. Nó nhìn ảnh một lần rồi dự đoán luôn, nên nhanh nhất.
>
> Faster R-CNN là hai giai đoạn, nặng nhất với hơn 41 triệu tham số. Nó xử lý qua hai bước nên chính xác, nhóm em dùng làm mốc chuẩn về độ chính xác.
>
> RT-DETR là transformer, khoảng 33 triệu tham số, chạy end-to-end và bỏ được bước hậu xử lý lọc hộp trùng, gọi là NMS, mà hai mô hình kia bắt buộc phải có.
>
> Tóm lại: một cái nhanh, một cái chính xác để làm chuẩn, một cái hiện đại.
>
> *(Chuyển slide)* Đã biết chọn ba mô hình nào rồi, thì câu hỏi tiếp theo là bên trong chúng hoạt động khác nhau ra sao. Em xin sang phần kiến trúc."

### Giải thích sâu

- Ba nhánh **một giai đoạn / hai giai đoạn / DETR** là ba hướng lớn nhất của object detection; nêu đủ ba cho thấy nhóm nắm được bức tranh tổng thể chứ không chỉ chạy thử vài model.
- Cả ba dùng **chung 3 lớp** (`motorbike`, `helmet`, `non-helmet`), **chung ảnh 640×640**, **chung cách chia train/val/test** — nhờ vậy so sánh mới sòng phẳng.
- Số tham số đã ngầm báo trước kết luận: nặng hơn thường chậm hơn.

---

## SLIDE 2 — Bên trong mỗi mô hình hoạt động thế nào

### Script

> *(Chỉ vào hình YOLO)*
>
> "Em xin nói nhanh cấu trúc bên trong.
>
> YOLO gồm backbone, neck và head. Backbone trích đặc trưng, neck gom đặc trưng ở nhiều tỉ lệ — chỗ này quan trọng với bài của nhóm em, vì đầu người ở xa rất nhỏ còn xe ở gần thì to. Head dự đoán thẳng hộp và lớp ngay tại từng vị trí, tất cả trong một lượt chạy nên rất nhanh. Đổi lại, nó sinh ra nhiều hộp chồng nhau cho cùng một vật, nên cuối cùng phải có một bước lọc tên là NMS: trong đám hộp chồng nhau đó, giữ lại hộp có điểm tin cậy cao nhất rồi bỏ những hộp còn lại.
>
> *(Chỉ vào hình Faster R-CNN)*
>
> Ngược lại với kiểu làm một lượt của YOLO, Faster R-CNN chia hẳn hai giai đoạn. Giai đoạn một, mạng RPN quét ảnh và đề xuất những vùng nghi có vật thể. Giai đoạn hai, từng vùng đó mới được phân loại và chỉnh lại hộp cho khít. Soi kỹ như vậy nên chính xác, nhưng chậm.
>
> *(Chỉ vào hình RT-DETR)*
>
> Còn RT-DETR thì đi hẳn một hướng khác. Nó dùng attention nên nhìn được toàn cảnh, rồi decoder có các object query — có thể hình dung mỗi query như một chỗ trống, tự đi gắp về đúng một vật thể. Vì lúc huấn luyện nó ghép một query với đúng một vật, không cho trùng, nên khi chạy không cần NMS. Đó là ý nghĩa của end-to-end.
>
> *(Chỉ vào ô Lý do chọn YOLO)*
>
> Và đây là kết luận phần mô hình: nhóm em chọn YOLO để triển khai, vì nó nhanh nhất, khoảng 40 hình một giây, mà mAP và recall vẫn đứng đầu. Với camera chạy thời gian thực thì tốc độ là yếu tố quyết định.
>
> *(Chuyển slide)* Nhưng ba mô hình này chỉ so sánh được sòng phẳng khi cùng được huấn luyện và dò siêu tham số theo một quy trình chung. Em xin sang phần cấu hình huấn luyện."

### Giải thích sâu (dễ bị hỏi)

- **Backbone / Neck / Head**: từ khóa chuẩn của detector; Neck kiểu FPN/PAN để trộn đặc trưng đa tỉ lệ, rất hợp bài này vì kích thước vật rất chênh nhau.
- **Anchor (Faster R-CNN)**: những khung mẫu đặt sẵn ở mỗi điểm; RPN chỉ cần chỉnh từ anchor ra vùng đề xuất, dễ học hơn là đoán hộp từ số 0.
- **RoI Align**: cắt một vùng kích thước bất kỳ về feature cố định (vd 7×7) rồi mới phân loại — khớp tọa độ chính xác hơn RoI Pooling cũ.
- **Object query & attention (RT-DETR)**: cách nói an toàn khi bị hỏi — "mỗi query là một vector học được, qua các lớp cross-attention nó chú ý vào một vùng ảnh và xuất ra một vật thể; số query cố định, cộng với việc ghép một-một lúc train, nên model đoán thẳng cả tập kết quả và không cần NMS".
- **Vì sao YOLO thắng dù RT-DETR chính xác gần bằng**: đây là đánh đổi tốc độ–độ chính xác. RT-DETR chỉ khoảng 4 FPS, Faster R-CNN khoảng 12 FPS, còn YOLO tầm 40 FPS mà chất lượng vẫn dẫn đầu.
- **NMS là gì**: sau khi model nhả nhiều hộp cho cùng một vật, NMS giữ hộp điểm cao nhất và bỏ các hộp trùng. YOLO với Faster R-CNN cần bước này; RT-DETR thì không.

---

## SLIDE 3 — Cách huấn luyện và dò siêu tham số bằng Ray Tune

### Script

> "Cuối cùng là cách huấn luyện và dò siêu tham số.
>
> Cả ba mô hình đều tinh chỉnh từ pretrained chứ không train từ số 0, vì dữ liệu train chỉ khoảng hai nghìn ảnh — train từ đầu vừa dễ overfit vừa tốn tài nguyên.
>
> Có mô hình xuất phát rồi, việc còn lại là chọn siêu tham số. Chỗ này nhóm em dùng Ray Tune, làm hai pha để tránh rò rỉ dữ liệu. Pha một, chỉ đánh giá trên validation, tuyệt đối không đụng tập test. Pha hai, lấy cấu hình tốt nhất rồi train lại từ đầu, sau đó mới đánh giá test đúng một lần. Nhờ vậy con số trên test mới khách quan.
>
> Vậy dò những gì và dò thế nào. Không gian tìm kiếm gồm learning rate, batch size và weight decay; riêng learning rate lấy mẫu theo thang log để rải đều qua nhiều bậc độ lớn. Nhóm em dùng random search, mỗi mô hình mười lần thử, cho chạy hai lần thử song song trên hai GPU của Kaggle.
>
> Một chi tiết đáng nói: chỉ Faster R-CNN được gắn thêm bộ lập lịch ASHA để bỏ sớm những lần thử kém, vì chỉ nó báo validation loss sau từng epoch. YOLO và RT-DETR chỉ báo kết quả ở cuối nên chạy hết cả mười lần.
>
> Về chỉ số, YOLO và RT-DETR tối ưu theo mAP càng cao càng tốt, còn Faster R-CNN theo validation loss càng thấp càng tốt. Batch của Faster R-CNN và RT-DETR chỉ để bằng 2 vì hai mô hình này nặng, GPU không tải nổi batch lớn.
>
> *(Chỉ vào bảng cấu hình tốt nhất)*
>
> Đây là cấu hình tốt nhất tìm được. Tóm lại, nhóm em so sánh công bằng ba trường phái, dò siêu tham số bài bản có tách riêng validation và test, và chọn YOLO vì cân bằng tốt nhất giữa tốc độ và độ chính xác. Em xin sang phần kết quả."

### Giải thích sâu — Không gian tìm kiếm thật (`raytune.py`)

| Mô hình | Learning rate | Batch | weight_decay | Riêng |
|---|---|---|---|---|
| **YOLO** | `lr0` log-uniform `[1e-4, 1e-2]` | {8, 16, 32} | log-uniform `[1e-5, 1e-3]` | `lrf` uniform `[0.01, 0.2]` |
| **Faster R-CNN** | `lr` log-uniform `[1e-4, 1e-2]` | {2, 4, 8} | log-uniform `[1e-5, 1e-3]` | `lr_step` {5,10,15}, `lr_gamma` {0.1, 0.5} |
| **RT-DETR** | `lr0` log-uniform `[1e-5, 1e-3]` | {4, 8, 16} | log-uniform `[1e-5, 1e-3]` | `lrf` uniform `[0.01, 0.2]` |

### Giải thích sâu — ASHA (Successive Halving) chạy thế nào

- Cho nhiều cấu hình cùng chạy ít epoch trước. Đến mỗi mốc, xếp hạng theo metric, giữ lại phần tốt nhất và loại phần còn lại; `reduction_factor=2` nghĩa là mỗi mốc giữ khoảng một nửa. Nhóm sống sót được cấp gấp đôi ngân sách epoch để chạy tiếp, lặp tới khi còn cấu hình tốt nhất.
- `grace_period=1`: mọi cấu hình được chạy tối thiểu 1 epoch rồi mới có thể bị cắt, để không giết oan cấu hình khởi động chậm. `max_t=20`: ngân sách epoch tối đa mỗi trial khi tune.
- Việc chạy **2 trial song song trên 2 GPU** là do đặt `max_concurrent=2` (mỗi trial xin 1 GPU), và điều này áp dụng cho **cả ba mô hình**, không riêng gì ASHA.
- "Asynchronous" của ASHA nói về chuyện khác: nó **không dựng rào đồng bộ** giữa các mốc — trial nào tới mốc trước thì xét cắt/giữ ngay, GPU vừa trống là bốc trial kế tiếp vào chạy luôn, nên hai GPU gần như không phải chờ nhau.
- Vì sao chỉ Faster R-CNN dùng được: ASHA cần metric báo theo từng epoch. Faster R-CNN có `on_epoch_end()` report `val_loss`; YOLO/RT-DETR (Ultralytics) chỉ trả mAP một lần ở cuối trial nên không có gì để cắt sớm, để `scheduler=None`.

### Giải thích sâu — vì sao lấy mẫu learning rate theo log

Learning rate trải qua nhiều bậc độ lớn (0.0001 → 0.01). Lấy mẫu tuyến tính sẽ dồn hầu hết mẫu vào vùng lớn; lấy mẫu log-uniform rải đều số mẫu qua mỗi bậc nên khám phá công bằng hơn, không bỏ sót vùng learning rate nhỏ.

### Giải thích sâu — hàm mất mát từng mô hình

- **YOLO**: Box + Cls + DFL. DFL (Distribution Focal Loss) mô hình hóa mỗi cạnh hộp thành một phân phối xác suất thay vì một số, giúp hồi quy tọa độ mượt và chính xác hơn.
- **Faster R-CNN**: RPN loss (ở giai đoạn 1) cộng RoI loss (ở giai đoạn 2) — mất mát ở cả hai giai đoạn.
- **RT-DETR**: GIoU + L1 cho vị trí và kích thước hộp, Cls cho phân loại; gắn với so khớp một-một Hungarian giữa query và ground-truth.

### Giải thích sâu — cấu hình tốt nhất (số thật từ `best_configs/*.json`)

| Mô hình | Optimizer | learning rate | batch | epoch | Khác |
|---|---|---|---|---|---|
| **YOLO (yolo26m)** | tự chọn (Ultralytics) | `1.11e-4` | 32 | 50 | lrf `0.177`, wd `1.2e-4` |
| **Faster R-CNN** | SGD, momentum 0.9 | `1.80e-3` | 2 | 50 | lr_step 15, gamma 0.1, wd `1.9e-4` |
| **RT-DETR** | AdamW | `2.41e-4` | 2 | 40–50 | lrf `0.033`, wd `1.4e-4` |

---

## Bảng Kết quả (đọc khớp nếu slide sau có)

| Mô hình | mAP@0.5 | mAP@0.5:0.95 | AR/Recall | FPS |
|---|---|---|---|---|
| **YOLO** | **0.78** | **0.54** | **0.86** | **40** |
| Faster R-CNN | 0.73 | 0.50 | 0.72 | 12 |
| RT-DETR | 0.76 | 0.53 | 0.84 | 4 |

> YOLO dẫn đầu cả ba chỉ số chất lượng lẫn tốc độ nên được chọn triển khai. RT-DETR bám sát về mAP nhưng chỉ 4 FPS, chưa hợp real-time; Faster R-CNN ổn định nhưng recall và tốc độ thấp hơn.

---

## Chuẩn bị Q&A

**"Vì sao không chọn Faster R-CNN dù nó là baseline chính xác?"**
> "Thật ra trên tập test của nhóm em, YOLO còn cao hơn cả về mAP lẫn recall, mà lại nhanh gấp khoảng ba lần, 40 so với 12 FPS. Faster R-CNN xử lý hai giai đoạn và soi từng vùng nên chậm, không hợp camera chạy trực tiếp."

**"RT-DETR bỏ được NMS nhờ đâu?"**
> "Nhờ cách ghép một-một lúc huấn luyện: mỗi vật thể chỉ gán cho đúng một query, nên khi chạy model không sinh hộp trùng, khỏi cần lọc NMS. Đó là ý nghĩa end-to-end."

**"Ray Tune chống overfitting với rò rỉ test thế nào?"**
> "Nhóm em dò chỉ trên validation, test không đụng tới. Có cấu hình tốt nhất rồi mới train lại từ đầu và đánh giá test đúng một lần, nên con số test là ước lượng khách quan."

**"ASHA khác random hay grid search thuần ở đâu, và sao chỉ dùng cho Faster R-CNN?"**
> "Random hay grid thuần thì train hết mọi cấu hình tới cùng, rất tốn. ASHA cắt sớm những cấu hình kém dựa trên kết quả giữa chừng. Mà muốn cắt giữa chừng thì cần metric báo theo từng epoch — chỉ pipeline Faster R-CNN có report val_loss mỗi epoch, còn YOLO với RT-DETR chỉ báo ở cuối nên phải chạy đủ trial."

**"Sao batch chỉ để 2 cho hai mô hình kia?"**
> "GPU Kaggle là Tesla T4 khoảng 16GB. ResNet50-FPN và transformer decoder tốn bộ nhớ, batch lớn là tràn; YOLO nhẹ nên để batch 32 được."

**"Metric để tune của ba mô hình có khác nhau không?"**
> "Có. YOLO với RT-DETR tối ưu theo mAP, càng cao càng tốt; Faster R-CNN tối ưu theo validation loss, càng thấp càng tốt, vì nó báo loss theo từng epoch."

---

## Bản rút gọn (nếu bị hối giờ)

> "Nhóm em thử ba trường phái: YOLO một giai đoạn thì nhanh, Faster R-CNN hai giai đoạn làm baseline chính xác, RT-DETR transformer thì hiện đại và bỏ được NMS. Cả ba đều tinh chỉnh từ mô hình pretrained trên khoảng hai nghìn ảnh. Siêu tham số thì dò bằng Ray Tune theo hai pha, dò trên validation còn test chỉ đánh giá một lần; dùng random search, riêng Faster R-CNN thêm ASHA để bỏ sớm cấu hình kém. Cuối cùng YOLO tốt nhất cả về độ chính xác lẫn tốc độ, tầm 40 FPS, nên nhóm em chọn nó để triển khai."
