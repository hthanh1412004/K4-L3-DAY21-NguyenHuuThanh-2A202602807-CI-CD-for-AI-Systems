# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| | |
|---|---|
| Họ và tên | Nguyen Huu Thanh |
| MSSV | 2A202602807 |
| Lớp / Khóa | K4 |
| Repo GitHub | https://github.com/hthanh1412004/K4-L3-DAY21-NguyenHuuThanh-2A202602807-CI-CD-for-AI-Systems |
| Ngày thực hiện | 07/10/2026 |

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---|---|---|---|---|
| 1 | 100 | 0.1 | 3 | 0.7407 | 0.8600 |
| 2 | 50 | 0.05 | 2 | 0.7083 | 0.8600 |
| 3 | 200 | 0.1 | 5 | 0.7368 | 0.8600 |

**Đã chọn:** `n_estimators=100`, `learning_rate=0.1`, `max_depth=3`.
Bộ này đạt F1 cao nhất. Ba cấu hình cùng accuracy, nên accuracy không phân biệt được chất lượng.
Ngưỡng chọn là 0.30, nâng F1 từ 0.7109 tại 0,5 lên 0.7407.
Holdout không tham gia fit nhưng dùng chọn tham số/ngưỡng; cần test set độc lập khi đánh giá sản phẩm.

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Chỉ 24,8% dữ liệu có thu nhập cao. Luôn đoán thu nhập thấp vẫn đạt accuracy 75,2%
nhưng F1 lớp dương bằng 0. F1 cân bằng precision và recall của lớp thu nhập cao;
quality gate dùng F1 ≥ 0,65.
Giả định dùng mô hình chọn khách hàng cho ưu đãi cao cấp, gán nhầm người thu nhập thấp
tăng chi phí tiếp thị nên precision thấp tốn kém hơn; mục đích khác có thể ưu tiên recall.
Confusion matrix và số đo từng lớp nằm trong detail.txt.

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| Python/SQLAlchemy quá mới | MLflow 2.13 thiếu API tương thích. | Dùng Python 3.11, SQLAlchemy 2.0, NumPy 1.26.4. |
| Release ban đầu lỗi | EC2 thiếu service. | Bootstrap systemd trong workflow; chạy lại thành công. |

## 4. So Sánh Bước 2 và Bước 3

**Số liệu từ artifact GitHub Actions thật; cả bốn jobs đều xanh.**

| | f1_score | accuracy |
|---|---|---|
| Bước 2 (22.361 mẫu) | 0.7407 | 0.8600 |
| Bước 3 (44.722 mẫu) | 0.7345 | 0.8800 |

F1 giảm 0.0062; dữ liệu mới cùng nguồn nên thêm mẫu không bảo đảm cải thiện.
Bonus 4 giữ model cũ trên S3 khi F1 giảm; log xác nhận chặn triển khai bước 3.
DVC push hoàn tất trước commit dữ liệu; commit tự kích hoạt pipeline.
API tại `13.220.141.198:8080` trả HTTP 200 cho healthz/score.
Model yếu trên nhánh riêng đạt F1 0,3974: Quality Gate thất bại, Release bị bỏ qua.

## 5. Phần Bonus Đã Thực Hiện

- [ ] Bonus 1: Có cấu hình DagsHub; cần token để xác minh remote run.
- [x] Bonus 2: Quét 17 ngưỡng, log MLflow và lưu ngưỡng trong model/API.
- [x] Bonus 3: Có confusion matrix, precision/recall và upload artifact trong workflow.
- [x] Bonus 4: Đã chặn F1 giảm trên cloud và kiểm thử rollback artifact.
- [x] Bonus 5: Kiểm tra tỷ lệ lớp trước fit, cảnh báo lệch quá 5 điểm phần trăm.
