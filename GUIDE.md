huẩn bị môi trường và dữ liệu bài toán
Về bài lab này
Xây dựng pipeline MLOps hoàn chỉnh: theo dõi thử nghiệm thực tế cục bộ bằng MLflow, quản lý phiên bản dữ liệu bằng DVC, tự động hóa CI/CD 4 giai đoạn trên GitHub Actions với Quality Gate f1 >= 0.65, triển khai FastAPI REST API trên Cloud VM và kích hoạt huấn luyện liên tục khi có dữ liệu mới.
Bạn làm được gì sau bài này
Thiết lập quá trình theo dõi thí nghiệm máy học bằng MLflow trên máy tính cá nhân.
Quản lý và phiên bản hóa dữ liệu bằng DVC với cloud object storage (GCP / AWS / Azure) làm remote.
Xây dựng pipeline CI/CD hoàn chỉnh trên GitHub Actions với bốn giai đoạn: kiểm thử, huấn luyện, kiểm tra chất lượng, triển khai.
Triển khai mô hình lên máy chủ ảo trên cloud (GCE / EC2 / Azure VM) dưới dạng REST API bằng FastAPI.
Chọn đúng chỉ số đánh giá cho bài toán có phân bố lớp mất cân bằng (F1-score thay vì Accuracy).
Mô phỏng quy trình huấn luyện liên tục: bổ sung dữ liệu mới và kích hoạt pipeline tự động.
Cần chuẩn bị
Python 3.10 trở lên trên máy tính cá nhân.
Git và tài khoản GitHub cá nhân.
Tài khoản Cloud (chọn một trong ba: GCP, AWS, hoặc Azure, gói miễn phí/trial) kèm CLI tương ứng (gcloud, aws, hoặc az).
Python 3.10+, pip, venv
Git, GitHub Actions
DVC, MLflow
Cloud CLI (gcloud / aws / az), Cloud Object Storage (GCS / S3 / Azure Blob), Cloud VM (GCE / EC2 / Azure VM)
FastAPI, Uvicorn, Scikit-learn, Pytest, Curl, SSH
Lỗi thường gặp
dvc push thất bại do lỗi xác thực → Kiểm tra biến môi trường hoặc credentialpath trỏ đúng file key (sa-key.json với GCP).
GitHub Actions dvc pull thất bại → Xác nhận GitHub secret STORAGE_CREDENTIALS chứa toàn bộ nội dung JSON key hợp lệ không sót ký tự.
Pipeline Bước 3 không được kích hoạt → Commit file con trỏ .dvc thay vì file CSV; kiểm tra file CSV đã được đưa vào .gitignore.
Quality gate bị chặn dù accuracy cao → Kiểm tra f1_score tính riêng cho lớp dương (không dùng average), tinh chỉnh siêu tham số mô hình.
Inference service trên VM không khởi động → Kiểm tra log bằng sudo journalctl -u income-api -n 50, kiểm tra file model.joblib trên Cloud Storage và biến ARTIFACT_BUCKET.
Bài thực hành này hướng dẫn bạn xây dựng hệ thống MLOps từ bước huấn luyện ban đầu đến triển khai tự động. Bạn sẽ theo dõi siêu tham số bằng MLflow trên máy cá nhân, quản lý phiên bản dữ liệu bằng DVC trên Cloud Storage, thiết lập pipeline kiểm thử, huấn luyện, kiểm tra chất lượng và triển khai trên GitHub Actions, sau đó kiểm tra quy trình tự động chạy lại khi có dữ liệu mới.

Kiến trúc hệ thống
Kiến trúc hệ thống MLOps
Pipeline CI/CD 4 Jobs

git push

Trigger tự động

dvc pull / upload model

Restart service

Máy cá nhân: MLflow, DVC add

GitHub Repository

GitHub Actions Runner

Job 1: Unit Test

Job 2: Train (dvc pull)

Job 3: Quality Gate (f1 >= 0.65)

Job 4: Release (SSH deploy)

Cloud Storage (GCS/S3/Blob)

Cloud VM (FastAPI /score)

Bước này thiết lập môi trường phát triển cục bộ, tải tập dữ liệu Census Income và phân chia thành các phần huấn luyện, đánh giá độc lập trước khi huấn luyện mô hình.

Điều kiện sẵn sàng trước khi bắt đầu0/2

Máy tính đã cài đặt Python 3.10 trở lên và Git.

Đã có tài khoản Cloud (GCP, AWS hoặc Azure) và cài đặt công cụ CLI tương ứng.
Phân bố dữ liệu Census Income và độ đo Accuracy
Tập dữ liệu Adult / Census Income lấy từ dữ liệu điều tra dân số Hoa Kỳ năm 1994, dùng để dự đoán thu nhập của một người có trên 50.000 USD/năm (target = 1) hay không (target = 0). Sau khi lọc bỏ các dòng thiếu thông tin, bộ dữ liệu còn 45.222 mẫu với 10 đặc trưng nhân khẩu học và nghề nghiệp được mã hóa sẵn thành số nguyên: age, workclass, education_num, marital_status, occupation, relationship, sex, capital_gain, capital_loss, hours_per_week.

Dữ liệu có đặc điểm mất cân bằng lớp: chỉ 24,8% số người có thu nhập cao (target = 1), còn 75,2% thuộc nhóm thu nhập thấp (target = 0). Nếu một mô hình luôn dự đoán nhãn 0 cho mọi trường hợp, độ chính xác (accuracy) vẫn đạt 75,2% dù mô hình không nhận diện được trường hợp thu nhập cao nào. Vì vậy, hệ thống dùng chỉ số F1 của lớp dương làm căn cứ đánh giá và đặt ngưỡng cho Quality Gate.

Dữ liệu được chia thành 3 phần:

data/train_batch1.csv (22.361 mẫu): Dùng huấn luyện tại Bước 1 và Bước 2.
data/holdout.csv (500 mẫu): Tập đánh giá độc lập cố định, không dùng để huấn luyện.
data/train_batch2.csv (22.361 mẫu): Dữ liệu mới dùng mô phỏng Continuous Training ở Bước 3.
Khởi tạo môi trường ảo và chuẩn bị dữ liệu
Bài thực hành này là bài cá nhân. Bạn hãy fork repo đề bài về tài khoản GitHub của mình; bản fork đó chính là repo nộp bài. Vì vậy hãy đặt đúng tên bài nộp ngay từ lúc fork. Đầu ra cuối cùng là một repo GitHub public.

Mã nguồn khởi tạo bài Lab
GitHub Repository
Mã nguồn khởi tạo bài Lab
git clone https://github.com/VinUni-AI20k/K4-L3L4-Track2-Day21-CI-CD-for-AI-Systems.git

Mở repo đề bài ở trên, bấm Fork ở góc trên bên phải.
Ở trang Create a new fork, chọn Owner là tài khoản của bạn. Ô Repository name đổi thành tên theo mẫu K4-L3-DAY21-HoVaTen-MSSV-CI-CD-for-AI-Systems: họ tên không dấu, không khoảng trắng, ví dụ K4-L3-DAY21-NguyenVanAn-2A202601234-CI-CD-for-AI-Systems.
Bấm Create fork. Bản fork của một repo public cũng là public, đúng yêu cầu nộp bài.
Clone bản fork của bạn (không phải repo đề bài) về máy. Fork chỉ tạo bản sao trên GitHub, còn lab chạy trên laptop nên bạn cần code ở máy; mọi kết quả sau đó sẽ được git push ngược lên chính bản fork này. Clone rồi mở terminal ở thư mục gốc:
git clone https://github.com/<tài-khoản-của-bạn>/K4-L3-DAY21-<HoVaTen>-<MSSV>-CI-CD-for-AI-Systems.git
cd K4-L3-DAY21-<HoVaTen>-<MSSV>-CI-CD-for-AI-Systems
Chép
Nếu lỡ fork với tên mặc định, vào Settings → General → Repository name của bản fork để đổi tên, rồi clone theo tên mới. Kiểm tra bằng git remote -v: origin phải trỏ tới repo trên tài khoản của bạn, để mọi lần git push sau này đi thẳng vào bài nộp.

Tạo và kích hoạt môi trường ảo:
Kích hoạt môi trường ảo
Linux / macOS
Windows (PowerShell)
python3 -m venv .venv
source .venv/bin/activate
Chép
Cài đặt các thư viện cần dùng:
pip install -r requirements.txt
Chép
Chạy script xử lý và chia dữ liệu:
python prepare_data.py
Chép
Dấu hiệu hoàn thành
Màn hình console hiển thị:

train_batch1.csv : 22361 mau
holdout.csv : 500 mau
train_batch2.csv : 22361 mau
Ty le lop >50K : 24.8%
Chép
Kiểm tra thư mục data/ có đủ 3 tệp CSV trên.
Chạy thử nghiệm thực tế cục bộ và theo dõi bằng MLflow
Trong bước này, bạn cấu hình MLflow tracking cục bộ, hoàn thiện mã huấn luyện trong src/train.py, chạy tối thiểu 3 thí nghiệm với các bộ siêu tham số khác nhau và chọn bộ tham số đạt f1_score >= 0.65 trên MLflow UI.

Siêu tham số trong Gradient Boosting
Khi tinh chỉnh thuật toán GradientBoostingClassifier, bạn làm việc với 3 tham số trong params.yaml:

n_estimators: Số lượng cây quyết định được tạo qua các vòng boosting (gợi ý thử: 50, 100, 200).
learning_rate: Mức đóng góp của từng cây để bù trừ sai số của các cây trước (gợi ý thử: 0.05, 0.1, 0.2).
max_depth: Độ sâu tối đa của mỗi cây (gợi ý thử: 2, 3, 5).
Gradient Boosting huấn luyện cây sau để sửa lỗi cho cây trước, nên n_estimators và learning_rate có quan hệ đánh đổi trực tiếp: giảm learning_rate thường đòi hỏi tăng n_estimators để bù lại.

Lưu ý khi tính F1-score
Trong mã nguồn, gọi f1_score(y_eval, preds) để tính riêng cho lớp dương (target = 1). Không truyền average="macro" hoặc average="weighted", vì việc tính trung bình sẽ bị lớp đa số kéo điểm lên cao và che lấp hiệu quả thực trên lớp thiểu số.

Cấu hình biến môi trường MLflow
Thiết lập MLflow lưu trữ thông tin vào tệp SQLite cục bộ:

Cấu hình biến môi trường MLflow
Linux / macOS
Windows (PowerShell)
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
export MLFLOW_ARTIFACT_ROOT=./mlartifacts
Chép
Hoàn thiện src/train.py
Mở file src/train.py và hoàn thiện hàm train() theo các vị trí TODO:

Chạy 3 lần thử nghiệm và so sánh trên MLflow UI
Chạy 3 lần với các giá trị khác nhau trong file params.yaml:

Lần 1: Cấu hình mặc định (n_estimators: 100, learning_rate: 0.1, max_depth: 3).
python src/train.py
Chép
Lần 2: Mô hình nông và chậm (n_estimators: 50, learning_rate: 0.05, max_depth: 2). Sửa params.yaml rồi chạy:
python src/train.py
Chép
Lần 3: Mô hình sâu hơn (n_estimators: 200, learning_rate: 0.1, max_depth: 5). Sửa params.yaml rồi chạy:
python src/train.py
Chép
Mở giao diện MLflow UI:
mlflow ui --backend-store-uri sqlite:///mlflow.db
Chép
Truy cập http://localhost:5000 trên trình duyệt.

Cách đọc kết quả trên MLflow UI
Nhấn nút Columns ở góc phải bảng để hiện các cột: f1_score, accuracy, n_estimators, learning_rate, max_depth. Sắp xếp bảng theo f1_score giảm dần. Bạn sẽ thấy accuracy giữa các lần chạy dao động không đáng kể (khoảng 85% đến 87%), nhưng f1_score thay đổi rõ rệt. Chọn bộ tham số có f1_score cao nhất (đạt từ 0.65 trở lên) và lưu vào params.yaml.

Xác nhận hoàn thành Bước 10/4

Tệp `outputs/report.json` và `models/model.joblib` đã được tạo.

MLflow UI hiển thị ít nhất 3 lần chạy với đầy đủ cột tham số và số đo.

Chụp ảnh MLflow UI lưu thành `nop-bai/anh-chup-man-hinh/01-mlflow-ui.png`.

Điền số liệu 3 lần chạy vào mục 1 của `nop-bai/bao-cao.md`.

Pipeline CI/CD tự động với DVC, Cloud VM và GitHub Actions
Bước này kết nối các thành phần vào pipeline tự động: quản lý dữ liệu bằng DVC trên Cloud Storage, viết API suy luận FastAPI trên Cloud VM, tạo unit test với pytest và hoàn thiện pipeline 4 jobs trên GitHub Actions kèm Quality Gate f1_score >= 0.65.

2.1 Quản lý dữ liệu bằng DVC và Cloud Storage
Đặt biến môi trường và tạo bucket (ví dụ với GCP, thay <PROJECT_ID> và <BUCKET_NAME>):
export PROJECT=<PROJECT_ID>
export BUCKET=<BUCKET_NAME>

gsutil mb -p $PROJECT -l us-central1 gs://$BUCKET
gcloud services enable storage.googleapis.com --project $PROJECT
Chép
Tạo Service Account và cấp quyền storage.objectAdmin trên đúng bucket của lab:
gcloud iam service-accounts create income-lab-sa \
 --display-name "Income Lab SA" \
 --project $PROJECT

gsutil iam ch \
 serviceAccount:income-lab-sa@$PROJECT.iam.gserviceaccount.com:roles/storage.objectAdmin \
  gs://$BUCKET

gcloud iam service-accounts keys create sa-key.json \
 --iam-account income-lab-sa@$PROJECT.iam.gserviceaccount.com
Chép
Cấu hình DVC trỏ remote đến Cloud Storage và đẩy dữ liệu lên:
dvc init
dvc remote add -d labstore gs://$BUCKET/dvc
dvc remote modify labstore credentialpath sa-key.json

dvc add data/train_batch1.csv
dvc add data/holdout.csv
dvc add data/train_batch2.csv

dvc push

git add data/train_batch1.csv.dvc data/holdout.csv.dvc data/train_batch2.csv.dvc .dvc/config .gitignore
git commit -m "feat: track datasets with DVC"
Chép
2.2 Viết API phục vụ suy luận trong src/serve.py
Mở file src/serve.py và hoàn thiện theo các vị trí TODO để server tải mô hình từ Cloud Storage khi khởi động, sau đó cung cấp hai endpoint: GET /healthz và POST /score.

2.3 Tạo Cloud VM và cấu hình systemd service
Tạo máy chủ Ubuntu trên Cloud và mở cổng 8080:
gcloud compute instances create income-api \
 --zone=us-central1-a \
 --machine-type=e2-small \
 --image-family=ubuntu-2204-lts \
 --image-project=ubuntu-os-cloud \
 --tags=income-api \
 --project $PROJECT

gcloud compute firewall-rules create allow-income-api \
 --allow=tcp:8080 \
 --target-tags=income-api \
 --project $PROJECT
Chép
Lấy IP công khai của VM (lưu lại biến VM_IP):
gcloud compute instances describe income-api \
 --zone=us-central1-a \
 --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
Chép
SSH vào VM, cài đặt thư viện cần thiết:
gcloud compute ssh income-api --zone=us-central1-a
Chép
Chạy tiếp trên VM:

sudo apt update && sudo apt install -y python3-pip
pip3 install fastapi uvicorn scikit-learn joblib google-cloud-storage
mkdir -p ~/models ~/src
exit
Chép
Chuyển file key và mã nguồn lên VM:
gcloud compute scp sa-key.json income-api:~/sa-key.json --zone=us-central1-a
gcloud compute scp src/serve.py income-api:~/src/serve.py --zone=us-central1-a
Chép
Cấu hình systemd service income-api trên VM:
gcloud compute ssh income-api --zone=us-central1-a
Chép
Chạy trong VM:

sudo tee /etc/systemd/system/income-api.service > /dev/null <<EOF
[Unit]
Description=Income Model Inference Server
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER
Environment="ARTIFACT_BUCKET=$BUCKET"
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/$USER/sa-key.json"
ExecStart=/usr/bin/python3 /home/$USER/src/serve.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable income-api
exit
Chép
Tạo cặp SSH key để GitHub Actions kết nối tới VM:
ssh-keygen -t ed25519 -f ~/.ssh/income_deploy -N "" -C "github-actions-deploy"
gcloud compute ssh income-api --zone=us-central1-a \
 --command "echo '$(cat ~/.ssh/income_deploy.pub)' >> ~/.ssh/authorized_keys"
Chép
2.4 Cấu hình 5 GitHub Secrets
Mở repository trên GitHub: Settings → Secrets and variables → Actions → Thêm đúng 5 secrets:

1. STORAGE_CREDENTIALS: Nội dung chuỗi JSON trong file sa-key.json.
2. ARTIFACT_BUCKET: Tên bucket đã tạo.
3. SERVER_HOST: Địa chỉ IP công khai của VM (VM_IP).
4. SERVER_USER: Tên tài khoản trên VM (lấy từ lệnh whoami trên VM).
5. SERVER_SSH_KEY: Nội dung private key trong file ~/.ssh/income_deploy.
   2.5 Viết unit test trong tests/test_train.py
   Mở file tests/test_train.py và hoàn thiện theo các vị trí TODO:

Chạy kiểm thử cục bộ:

pytest tests/ -v
Chép
2.6 Hoàn thiện pipeline trong .github/workflows/cicd.yml
Mở file .github/workflows/cicd.yml và điền các câu lệnh còn thiếu cho 4 jobs:

name: Income Model CI/CD

on:
push:
branches: [main]
paths: - 'data/**.dvc' - 'src/**.py' - 'params.yaml'
workflow_dispatch:

jobs:
unit-test:
name: Unit Test
runs-on: ubuntu-latest
steps: - uses: actions/checkout@v4 - uses: actions/setup-python@v5
with:
python-version: "3.10" - name: Install dependencies
run: pip install -r requirements.txt - name: Run unit tests
run: pytest tests/ -v

train:
name: Train
needs: unit-test
runs-on: ubuntu-latest
outputs:
f1: ${{ steps.read_report.outputs.f1 }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Authenticate to Cloud Storage
        run: |
          echo '${{ secrets.STORAGE_CREDENTIALS }}' > /tmp/sa-key.json
echo "GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa-key.json" >> $GITHUB_ENV
      - name: Pull data with DVC
        run: dvc pull data/train_batch1.csv.dvc data/holdout.csv.dvc
      - name: Train model
        run: python src/train.py
      - name: Read report
        id: read_report
        run: |
          F1=$(python -c "import json; d=json.load(open('outputs/report.json')); print(d['f1_score'])")
echo "f1=$F1" >> $GITHUB_OUTPUT - name: Upload model to Cloud Storage
env:
ARTIFACT_BUCKET: ${{ secrets.ARTIFACT_BUCKET }}
run: |
python - <<'PYEOF'
import os
from google.cloud import storage
client = storage.Client()
bucket = client.bucket(os.environ["ARTIFACT_BUCKET"])
blob = bucket.blob("artifacts/current/model.joblib")
blob.upload_from_filename("models/model.joblib")
print("Uploaded model.joblib successfully")
PYEOF - name: Save report as artifact
uses: actions/upload-artifact@v4
with:
name: report
path: outputs/report.json

quality-gate:
name: Quality Gate
needs: train
runs-on: ubuntu-latest
steps: - name: Check quality gate
run: |
python - <<'PYEOF'
f1 = float("${{ needs.train.outputs.f1 }}")
if f1 < 0.65:
raise SystemExit(f"FAILED: f1_score {f1:.4f} < 0.65. Huy trien khai.")
print(f"PASSED: f1_score {f1:.4f} >= 0.65. Dang trien khai model.")
PYEOF

release:
name: Release
needs: quality-gate
runs-on: ubuntu-latest
steps: - name: SSH deploy to VM
uses: appleboy/ssh-action@v1.0.3
with:
host: ${{ secrets.SERVER_HOST }}
username: ${{ secrets.SERVER_USER }}
key: ${{ secrets.SERVER_SSH_KEY }}
script: |
sudo systemctl restart income-api
sleep 5
curl -sf http://localhost:8080/healthz && echo "Health check passed." || exit 1
Chép
2.7 Kích hoạt và xác nhận hoàn thành Bước 2

1. Đẩy mã nguồn lên GitHub:
   git add .
   git commit -m "feat: complete CI/CD pipeline, tests, and serving API"
   git remote set-url origin https://github.com/<YOUR_GITHUB_USER>/<YOUR_REPO>.git
   git push -u origin main
   Chép
1. Kiểm tra tab Actions trên GitHub: xác nhận cả 4 jobs (Unit Test, Train, Quality Gate, Release) đều chuyển màu xanh.
1. Khởi động service trên VM (chỉ cần chạy một lần sau khi pipeline đưa model lên bucket):
   gcloud compute ssh income-api --zone=us-central1-a \
    --command "sudo systemctl start income-api"
   Chép
1. Gọi thử API từ máy cá nhân:

# Kiểm tra healthz

curl http://$VM_IP:8080/healthz

# Kết quả: {"status":"ok"}

# Dự đoán mẫu thu nhập thấp

curl -X POST http://$VM_IP:8080/score \
 -H "Content-Type: application/json" \
 -d '{"features": [60, 2, 5, 2, 4, 0, 1, 0, 0, 45]}'

# Kết quả: {"prediction": 0, "label": "thu_nhap_thap"}

# Dự đoán mẫu thu nhập cao

curl -X POST http://$VM_IP:8080/score \
 -H "Content-Type: application/json" \
 -d '{"features": [28, 2, 14, 2, 11, 0, 1, 0, 0, 45]}'

# Kết quả: {"prediction": 1, "label": "thu_nhap_cao"}

Chép
Xác nhận hoàn thành Bước 20/3

Chụp tab Actions hoàn thành 4 jobs màu xanh → `nop-bai/anh-chup-man-hinh/02-actions-buoc-2.png`.

Chụp màn hình terminal gọi 2 lệnh curl có IP của VM và kết quả trả về → `nop-bai/anh-chup-man-hinh/04-curl-api.png`.

Chụp Cloud Storage Console thấy rõ `dvc/` và `artifacts/current/model.joblib` → `nop-bai/anh-chup-man-hinh/05-cloud-storage.png`.

Huấn luyện liên tục khi có dữ liệu mới
Bước này mô phỏng quy trình nạp dữ liệu định kỳ: ghép thêm 22.361 mẫu mới, cập nhật DVC và đẩy commit để GitHub Actions tự động huấn luyện lại rồi cập nhật mô hình trên VM.

Cơ chế kích hoạt pipeline từ tệp con trỏ dữ liệu
Trong .github/workflows/cicd.yml, điều kiện kích hoạt được đặt theo đường dẫn:

paths:

- 'data/\*\*.dvc'
- 'src/\*\*.py'
- 'params.yaml'
  Chép
  Khi bạn thêm dữ liệu vào data/train_batch1.csv, DVC tính lại mã hash md5 và cập nhật tệp train_batch1.csv.dvc. Đẩy commit chứa thay đổi của tệp .dvc lên nhánh main sẽ kích hoạt GitHub Actions chạy lại toàn bộ quy trình mà không cần sửa code Python.

Nguyên tắc an toàn: dvc push trước git push
Bạn cần chạy dvc push trước khi chạy git push. Nếu đẩy Git commit lên trước, runner trên GitHub Actions sẽ chạy ngay và gọi dvc pull. Khi dữ liệu mới chưa có trên bucket, pipeline sẽ báo lỗi thiếu tệp và dừng lại.

Nạp dữ liệu mới và kích hoạt pipeline
Chạy script ghép dữ liệu:
python append_batch.py
Chép
Kiểm tra số dòng:

wc -l data/train_batch1.csv

# Kết quả: 44723 dòng (kể cả dòng tiêu đề)

Chép
Cập nhật DVC và đẩy dữ liệu lên Cloud Storage:
dvc add data/train_batch1.csv
dvc push
Chép
Commit tệp .dvc và push lên GitHub:
git add data/train_batch1.csv.dvc
git commit -m "data: bổ sung 22361 mẫu dữ liệu mới (train_batch2)"
git push origin main
Chép
Theo dõi pipeline và kiểm tra kết quả
Vào tab Actions trên GitHub để theo dõi lần chạy mới có tiêu đề "data: bổ sung 22361 mẫu dữ liệu mới (train_batch2)":

Job Train kéo 44.722 mẫu từ Cloud Storage, huấn luyện mô hình mới và tải artifact lên bucket.
Quality Gate kiểm tra điểm F1.
Release kết nối SSH vào Cloud VM và khởi động lại API server.
Kiểm tra lại suy luận từ terminal máy cá nhân:

curl -X POST http://$VM_IP:8080/score \
 -H "Content-Type: application/json" \
 -d '{"features": [28, 2, 14, 2, 11, 0, 1, 0, 0, 45]}'
Chép
So sánh kết quả Bước 2 và Bước 3
Tải report.json từ Artifacts của hai lần chạy ở Bước 2 và Bước 3 để điền vào mục 4 của nop-bai/bao-cao.md:

Chỉ số Bước 2 (22.361 mẫu) Bước 3 (44.722 mẫu)
f1_score (Kết quả thực tế) (Kết quả thực tế)
accuracy (Kết quả thực tế) (Kết quả thực tế)
Vì sao F1-score không tăng mạnh khi thêm dữ liệu
Hai tập dữ liệu được chia ngẫu nhiên từ cùng một nguồn điều tra dân số nên có chung phân phối. Khi mô hình đã học được các đặc trưng chính từ 22.000 mẫu đầu, việc nạp thêm dữ liệu cùng phân phối thường làm F1 dao động trong biên độ hẹp hoặc giảm nhẹ khoảng 0.01 do biến thiên ngẫu nhiên. Trọng tâm của bước này là kiểm chứng đường ống tự động chạy trọn vẹn từ commit dữ liệu đến triển khai thực tế.

Xác nhận hoàn thành Bước 30/2

Chụp ảnh GitHub Actions của lần chạy do commit dữ liệu kích hoạt (thấy rõ commit message của data) → `nop-bai/anh-chup-man-hinh/03-actions-buoc-3.png`.

Điền bảng so sánh và nhận xét vào mục 4 của `nop-bai/bao-cao.md`.

Kiểm tra trước khi nộp bài, rubic chấm điểm
Bước này hướng dẫn kiểm tra lại các tệp bằng chứng trong thư mục nop-bai/, đối chiếu tiêu chí rubric và gửi liên kết repository lên nền tảng VLearn.

Cấu trúc thư mục nop-bai/
Thư mục nop-bai/ trong repository gồm các tệp sau:

nop-bai/
├── README.md <- Danh sách tự kiểm tra
├── bao-cao.md <- Báo cáo ngắn (tối đa 1 trang A4)
└── anh-chup-man-hinh/
├── 01-mlflow-ui.png <- MLflow UI (Bước 1: từ 3 thí nghiệm, có F1 và Accuracy)
├── 02-actions-buoc-2.png <- GitHub Actions Bước 2 (4 jobs xanh)
├── 03-actions-buoc-3.png <- GitHub Actions Bước 3 (kích hoạt bởi commit data)
├── 04-curl-api.png <- Terminal gọi curl /healthz và /score tới VM IP (Bước 2)
└── 05-cloud-storage.png <- Cloud Storage Console thấy dvc/ và model.joblib (Bước 2)
Chép
Rubric chấm điểm chính (80 điểm)
Hạng mục Tiêu chí đánh giá Điểm tối đa
Bước 1: MLflow tracking MLflow UI hiển thị ít nhất 3 lần chạy với các siêu tham số khác nhau 12
Bước 1: Độ đo Mỗi lần chạy ghi nhận đủ cả f1_score và accuracy 8
Bước 1: Phân tích Xác định bộ siêu tham số tốt nhất và giải thích vì sao dùng F1 thay vì accuracy 4
Bước 2: DVC Remote đã cấu hình, dvc push thành công, dữ liệu hiển thị trên cloud storage 12
Bước 2: CI/CD Cả bốn GitHub Actions jobs (Unit Test, Train, Quality Gate, Release) đều qua (màu xanh) 16
Bước 2: Quality gate Release job tự động bị chặn khi f1_score dưới ngưỡng 0.65 4
Bước 2: Serving VM trả về kết quả đúng tại endpoint POST /score 12
Bước 3: Tự động hóa Một commit dữ liệu mới kích hoạt toàn bộ pipeline không cần tác động thủ công 12
Tổng 80
Các thử thách nâng cao (Bonus, tối đa 20 điểm)

1. Bonus 1: Tracking MLflow từ xa với DagsHub (4 điểm): Kết nối MLflow đến server DagsHub thay vì file sqlite cục bộ.
2. Bonus 2: Điều chỉnh ngưỡng quyết định (4 điểm): Quét ngưỡng xác suất từ 0.1 đến 0.9 để tìm F1 tối ưu thay vì ngưỡng 0.5.
3. Bonus 3: Báo cáo Precision / Recall tự động (4 điểm): Tự động tính confusion matrix, precision/recall theo lớp và lưu artifact.
4. Bonus 4: Hoàn trả về phiên bản trước (Rollback) (4 điểm): So sánh F1 mới với F1 cũ trên bucket, chỉ release khi F1 mới >= F1 cũ.
5. Bonus 5: Cảnh báo lệch lạc dữ liệu (Data Drift) (4 điểm): Cảnh báo nếu tỷ lệ lớp dương lệch quá 5% so với mốc 24.8%.
   Yêu cầu viết báo cáo nop-bai/bao-cao.md
   Mở tệp nop-bai/bao-cao.md và hoàn thiện các mục theo quy định:

6. Bộ siêu tham số đã chọn và lý do: Ghi lại kết quả thực tế từ MLflow UI và phân tích đánh đổi giữa các tham số.
7. Vì sao Quality Gate đặt trên F1 thay vì Accuracy: Diễn giải dựa trên tỷ lệ 24,8% lớp dương.
8. Khó khăn gặp phải và cách giải quyết: Nêu 2 đến 3 vấn đề kỹ thuật gặp phải (quyền bucket, kết nối SSH, secrets...).
9. So sánh Bước 2 và Bước 3: Điền số liệu F1/Accuracy và phân tích trung thực (2-3 câu).
10. Phần Bonus đã thực hiện (nếu có): Đánh dấu [x] vào các thử thách đã làm (Bonus 1 đến Bonus 5) và mô tả ngắn gọn cách triển khai (tối đa 1 dòng mỗi mục). Nếu không thực hiện bonus, hãy xóa toàn bộ Mục 5 để giữ độ dài báo cáo trong 1 trang A4.
    Quy định độ dài báo cáo
    Xóa toàn bộ các khối chú thích <!-- ... --> trong file bao-cao.md sau khi điền xong. Báo cáo không vượt quá 1 trang A4 (khoảng 450 đến 550 từ). Kiểm tra số từ bằng:

wc -w nop-bai/bao-cao.md
Chép
Nộp bài lên VLearn

1. Nén ảnh chụp màn hình dưới 1MB mỗi ảnh và commit vào Git.
2. Đẩy toàn bộ thư mục nop-bai/ lên GitHub:
   git add nop-bai/
   git commit -m "docs: finalize submission report and screenshots"
   git push origin main
   Chép
3. Mở trình duyệt ẩn danh để kiểm tra repository đã ở chế độ public và người chấm xem được nội dung.
4. Sao chép link repository GitHub công khai và dán vào ô nộp bài tại: https://vlearn.dev
   Checklist hoàn thành bài Lab0/4

Repo GitHub ở chế độ public và chứa mã nguồn hoàn chỉnh (`src/`, `tests/`, `.github/`, con trỏ DVC).

Đủ 5 ảnh chụp màn hình đúng tên và đúng nội dung trong `nop-bai/anh-chup-man-hinh/`.

`nop-bai/bao-cao.md` được điền đủ các mục bắt buộc, có cập nhật hoặc lược bỏ mục Bonus, không quá 1 trang A4 và đã xóa hết chú thích hướng dẫn.

Đã nộp URL GitHub repo lên https://vlearn.dev.

Nộp bài và đánh giá Lab
Dán link GitHub, Drive hoặc LMS của bài đã nộp. Mỗi lab giữ một bài; nộp lại sẽ ghi đè.

Hạn nộp: 07/10/2026 23:59 (giờ Việt Nam)

Đánh giá Lab này \*

1 = chưa tốt · 5 = rất tốt
Link bài đã nộp \*
https://github.com/…
Xác nhận đã nộp
