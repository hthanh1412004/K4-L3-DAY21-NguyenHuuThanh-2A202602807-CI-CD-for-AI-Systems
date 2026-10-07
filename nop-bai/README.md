# Nộp Bài - Day 21: CI/CD cho AI Systems

Thư mục này là nơi chứa **bằng chứng nộp bài**. Bạn không cần tạo thêm thư mục nào khác:
điền vào các file có sẵn và bỏ ảnh chụp màn hình vào đúng tên file đã quy định.

## Trạng thái thực hiện 07/10/2026

- Đã hoàn thiện mã huấn luyện, API, workflow 4 jobs và bonus 2–5.
- 22 kiểm thử đã qua; kết quả XML và số liệu thực nghiệm thật nằm trong [ket-qua/](ket-qua/).
- 3 thí nghiệm MLflow và lần huấn luyện với 44.722 mẫu đã chạy cục bộ; tham số tốt nhất
  là 100 cây, learning_rate 0,1, max_depth 3, ngưỡng 0,30, F1 0,7407.
- S3 riêng tư `income-lab-405134482332-20261007` chứa dữ liệu DVC và model.
- [Bước 2](https://github.com/hthanh1412004/K4-L3-DAY21-NguyenHuuThanh-2A202602807-CI-CD-for-AI-Systems/actions/runs/37608754832)
  và [bước 3](https://github.com/hthanh1412004/K4-L3-DAY21-NguyenHuuThanh-2A202602807-CI-CD-for-AI-Systems/actions/runs/37609415881)
  đều qua cả bốn jobs. Bước 3 do commit dữ liệu tự kích hoạt sau DVC push.
- API trên EC2 tại `http://13.220.141.198:8080`: healthz/score đều HTTP 200.
- F1 bước 3 là 0,7345 < 0,7407; bonus 4 giữ model bước 2, có log và report S3 xác nhận.
- [Lần thử gate](https://github.com/hthanh1412004/K4-L3-DAY21-NguyenHuuThanh-2A202602807-CI-CD-for-AI-Systems/actions/runs/37609536074)
  trên nhánh riêng đạt F1 0,3974: gate thất bại, Release skipped đúng thiết kế.
- Ảnh 01–04 và 07 là cửa sổ thật; ảnh trình duyệt có thanh địa chỉ.
- Người học chọn tự bổ sung ảnh S3 số 05. Bonus 1 chờ tài khoản/token DagsHub.
- Báo cáo dùng artifact CI thật. Chưa nộp URL lên VLearn.

Các bước kết nối tài khoản và chạy tiếp: [huong-dan-chay.md](huong-dan-chay.md).

```
nop-bai/
├── README.md                  <- file này (checklist)
├── bao-cao.md                 <- template báo cáo, không quá 1 trang A4
└── anh-chup-man-hinh/
    ├── README.md              <- mô tả yêu cầu của từng ảnh
    ├── 01-mlflow-ui.png
    ├── 02-actions-buoc-2.png
    ├── 03-actions-buoc-3.png
    ├── 04-curl-api.png
    └── 05-cloud-storage.png
```

---

## Checklist Trước Khi Nộp

Đánh dấu `[x]` khi hoàn thành từng mục:

- [x] Repo GitHub ở chế độ **public** và chứa toàn bộ code, cấu hình đã hoàn thiện.
- [ ] Đủ 5 ảnh trong `anh-chup-man-hinh/`, đúng tên file, đúng thứ tự (xem
      [yêu cầu chi tiết](anh-chup-man-hinh/README.md)).
- [ ] `bao-cao.md` đã điền đủ 3 mục bắt buộc và không vượt quá 1 trang A4.
- [x] Đã `git push` phần code, báo cáo và minh chứng hiện có lên GitHub; ảnh S3 còn cần bổ sung.
- [ ] Dán URL repo GitHub vào bài nộp trên **https://vlearn.dev**.
- [ ] Mở lại URL vừa nộp ở chế độ ẩn danh để chắc chắn repo public và người chấm xem được.

---

## Ảnh Chụp Màn Hình Tương Ứng Với Rubric

| Ảnh | Chứng minh hạng mục nào trong rubric | Điểm |
|---|---|---|
| `01-mlflow-ui.png` | Bước 1 - MLflow tracking, Bước 1 - Độ đo | 20 |
| `02-actions-buoc-2.png` | Bước 2 - CI/CD (bốn jobs màu xanh) | 16 |
| `03-actions-buoc-3.png` | Bước 3 - Tự động hóa | 12 |
| `04-curl-api.png` | Bước 2 - Serving | 12 |
| `05-cloud-storage.png` | Bước 2 - DVC | 12 |

Phần `bao-cao.md` chứng minh hạng mục **Bước 1 - Phân tích** (4 điểm) và là nơi bạn giải
trình khi một ảnh nào đó chưa thể hiện đủ (ví dụ quality gate đã chặn đúng một lần).

---

## Quy Ước Chung

- **Định dạng ảnh**: `.png` (ưu tiên) hoặc `.jpg`. Nếu dùng `.jpg`, giữ nguyên phần tên,
  chỉ đổi đuôi — ví dụ `01-mlflow-ui.jpg`.
- **Không đổi số thứ tự đầu tên file.** Thứ tự này là thứ tự chấm bài.
- **Không che thông tin cần chấm**: tên job, trạng thái màu xanh, giá trị `f1_score`,
  đường dẫn bucket. Được phép che email cá nhân và khóa bí mật.
- **Cần chụp cả URL trên thanh địa chỉ** với các ảnh chụp từ trình duyệt (MLflow UI,
  GitHub Actions, Cloud Storage Console) để xác nhận đúng repo/project của bạn.
- **Tuyệt đối không commit khóa bí mật**: `sa-key.json`, nội dung GitHub Secrets, access
  key của cloud. Nếu ảnh lỡ chứa các thông tin này, hãy che lại trước khi commit.

---

## Ghi Chú Về Kích Thước Repo

Ảnh chụp màn hình được commit trực tiếp vào Git. Giữ mỗi ảnh dưới **1 MB** (chụp vùng cần
thiết thay vì toàn màn hình 4K, hoặc nén lại trước khi commit) để repo không phình to.

Nếu bạn dùng macOS, có thể nén nhanh bằng lệnh sẵn có:

```bash
sips -Z 1600 nop-bai/anh-chup-man-hinh/01-mlflow-ui.png
```
