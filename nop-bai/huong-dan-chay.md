# Chạy bản lab đã hoàn thiện

## Kết quả đã xác minh

- Hai pipeline bước 2 và 3 đều qua bốn jobs; xem `ket-qua/buoc-*-actions.json`.
- API: `http://13.220.141.198:8080/docs`; healthz/score đã trả HTTP 200.
- S3: `income-lab-405134482332-20261007`, region `us-east-1`.
- Bonus 1 đã xác minh qua CI run `37638208781`; DagsHub run
  `fffe5f3425174cf48867fc4be3539671` Finished, F1 0,7345, accuracy 0,88.
  Số liệu lưu trong `ket-qua/buoc-dagshub-report.json`; ảnh 06 là giao diện remote thật.
- Dữ liệu hiện tại có 44.722 mẫu; không chạy lại `prepare_data.py` hoặc bộ thí nghiệm
  batch 1 trên dữ liệu này. Muốn tái hiện bước 1, checkout con trỏ ở commit `99dcf8f`
  trong clone riêng rồi `dvc pull`.
- Model production vẫn là bước 2 do F1 model bước 3 giảm. Đây là bonus 4 hoạt động đúng.

## Phần cục bộ

Trong PowerShell ở thư mục repo:

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
. ./scripts/activate_lab.ps1
.venv/Scripts/python prepare_data.py
.venv/Scripts/python -m pytest tests/ -v
.venv/Scripts/python -m scripts.run_experiments
.venv/Scripts/python -m scripts.write_report
.venv/Scripts/python -m src.serve
```

API tại `http://localhost:8080`. Trong terminal thứ hai:

```powershell
curl.exe http://localhost:8080/healthz
$payload = '{"features":[28,2,14,2,11,0,1,0,0,45]}'
Invoke-RestMethod -Method Post -Uri http://localhost:8080/score -ContentType application/json -Body $payload
.venv/Scripts/mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Mở `http://localhost:5000`, chọn experiment `adult-income`, hiện các cột F1,
accuracy, n_estimators, learning_rate, max_depth và chụp ảnh số 01.
`ket-qua/` chứa kết quả thí nghiệm cục bộ và artifact thực của hai pipeline cloud.

## Kết nối cloud và chạy GitHub Actions

1. Khi dựng lại lab, dùng bucket và VM thật, xác thực cloud trên máy.
2. Chạy `./scripts/configure_dvc.ps1 -Provider aws -Bucket TEN_BUCKET_THAT`
   (hoặc `-Provider gcp -Bucket TEN_BUCKET_THAT -CredentialPath DUONG_DAN_KEY`).
   Script cấu hình remote thực, tạo con trỏ và `dvc push`.
   Credential path được lưu trong `.dvc/config.local`, không đưa vào Git.
3. Chép repo vào `~/income-api` trên VM Ubuntu, export `ARTIFACT_BUCKET` và
   `CLOUD_PROVIDER`, chạy `bash scripts/setup_vm.sh`. Cấp quyền đọc/ghi bucket
   cho CI và quyền đọc bucket cho VM; dùng IAM role trên EC2 nếu có thể.
   Với GCP, thêm `GOOGLE_APPLICATION_CREDENTIALS=/duong/dan/key.json` vào
   `~/income-api/.env`; file này không được commit.
4. Mở cổng 8080 cho bài lab và cấu hình SSH deploy user được phép
   `sudo systemctl restart income-api` không cần nhập mật khẩu.
5. Thêm GitHub Secrets theo bảng sau. Lấy host key SSH qua kênh đáng tin cậy
   trên VM (`/etc/ssh/ssh_host_ed25519_key.pub`), rồi lưu dòng known_hosts
   gồm `IP ssh-ed25519 KEY` vào `SERVER_HOST_KEY`.

| Secret | Giá trị |
|---|---|
| STORAGE_CREDENTIALS | GCP: JSON service account; AWS: JSON có `aws_access_key_id`, `aws_secret_access_key`, và `aws_session_token` nếu dùng khóa tạm |
| ARTIFACT_BUCKET | Tên bucket thật |
| SERVER_HOST | IP hoặc hostname VM |
| SERVER_USER | User SSH trên VM |
| SERVER_SSH_KEY | Private key deploy, public key đã có trên VM |
| SERVER_HOST_KEY | Dòng known_hosts của VM đã kiểm tra |
| MLFLOW_TRACKING_URI | Bonus 1: `https://dagshub.com/OWNER/REPO.mlflow` |
| MLFLOW_TRACKING_USERNAME | Tài khoản DagsHub |
| MLFLOW_TRACKING_PASSWORD | Token DagsHub |

6. Với AWS, thêm repository variable `CLOUD_PROVIDER=aws`, `AWS_REGION=us-east-1`,
   `SERVER_SECURITY_GROUP` là ID security group EC2. CI cần quyền mở/đóng ingress
   trong đúng group để cho phép IP runner tạm thời. Khi chưa có DagsHub, MLflow dùng SQLite.
7. Commit code, `.dvc/config`, ba con trỏ `data/*.dvc`, báo cáo và bằng chứng;
   kiểm tra `dvc push` thành công trước `git push`. Chụp lần chạy Bước 2 (ảnh 02),
   kết quả curl tới VM (ảnh 04) và cloud storage (ảnh 05).
8. Khi Bước 2 chạy xong, chạy `./scripts/continuous_training.ps1`.
   Script ghép dữ liệu, cập nhật con trỏ, push DVC rồi commit/push Git để
   tự động kích hoạt Bước 3. Chụp ảnh 03 và thay số liệu cục bộ trong báo cáo
   bằng kết quả Actions nếu khác.

## Hành vi bonus

Ngưỡng 0,10–0,90 (bước 0,05) được chọn theo F1 trên holdout đúng yêu cầu lab,
lưu vào model và dùng trong API. Vì holdout được dùng để chọn tham số/ngưỡng,
điểm này có thiên lệch chọn mô hình; sản phẩm thực tế cần test set độc lập.
`detail.txt` chứa confusion matrix và precision/recall từng lớp.
Tỷ lệ target=1 lệch quá 5 điểm phần trăm so với 24,8% sẽ in cảnh báo.

Release chỉ ghi `artifacts/current/` sau khi F1 đạt 0,65 và không thấp hơn
report hiện hành. Model/report cũ được sao lưu vào `artifacts/previous/`;
nếu SSH hoặc health check thất bại, workflow phục hồi artifact rồi restart
model cũ. Lần chạy bị chặn do F1 giảm sẽ giữ model cũ, dù đã đạt ngưỡng 0,65.
Đây là hành vi Bonus 4; không được báo là model mới đã được triển khai.

## Nộp bài

Ảnh S3 05a/05b và DagsHub 06 đã được bổ sung. Ba secrets MLflow được cấu hình
trong GitHub Actions; `.env` cục bộ vẫn dùng MLflow SQLite.
Nộp URL repo public lên `https://vlearn.dev` bằng tài khoản học viên, rồi mở lại
URL đã nộp ở chế độ ẩn danh để kiểm tra người chấm truy cập được.
