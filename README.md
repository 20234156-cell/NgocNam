# VIETCREDIT — Hỗ trợ thẩm định tín dụng

Ứng dụng nội bộ FastAPI + HTML/CSS/JavaScript, phiên bản ứng dụng 1.3.0. Model **XGBoost-CreditRisk-v1.2.0** và ngưỡng **0,73 / 0,50** được giữ nguyên.

Đây là hệ thống hỗ trợ quyết định trên dữ liệu tổng hợp. Chưa được xác nhận cho phê duyệt tín dụng thực; chức năng Core Banking chỉ mô phỏng và không chuyển tiền. Không có AI Reviewer, Independent AI Supervisor, LLM API hay bộ quyết định giả lập trên trình duyệt.

Đối chiếu đề bài, logic và điều kiện nghiệm thu: [reports/assignment_review.md](reports/assignment_review.md).

## Chạy tại máy cá nhân

Dùng Python 3.13. Từ thư mục project:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.auth thamdinh --role "Loan Officer"
python -m src.auth quantriruiro --role "Risk Manager"
python -m src.auth chutich --role "Committee Chair"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --no-server-header
```

Mỗi lệnh tạo tài khoản yêu cầu nhập mật khẩu riêng, từ 12 đến 256 ký tự, không hiển thị ra màn hình. **Không có mật khẩu mặc định.** Chỉ tạo các tài khoản cần thiết. Sau đó mở http://127.0.0.1:8001/cockpit và đăng nhập. `run_server.bat` ưu tiên Python trong `.venv`, không bật reload hoặc mở mạng công cộng.

Đặt lại mật khẩu hoặc đổi vai trò bằng lệnh quản trị cục bộ:

```powershell
python -m src.auth thamdinh --role "Loan Officer" --replace
```

Lệnh này thu hồi các phiên đăng nhập cũ. Người có quyền sửa database hoặc chạy CLI quản trị phải là người được tin cậy.

## Quyền hạn

### Quản lý hồ sơ đã lưu

Sau khi thẩm định thành công, mở **Hồ sơ đã lưu** để tìm theo mã hồ sơ,
xem kết quả mới nhất và trạng thái quyết định hội đồng. Danh sách có 20 hồ sơ
mỗi trang. **Lịch sử / Chi tiết** hiển thị từng lần thẩm định, dữ liệu tài chính,
CIC, kết quả chính sách, đóng góp SHAP và quyết định hội đồng của lần đó.
**Mở kết quả mới nhất** nạp hồ sơ vào quy trình xem xét hiện có.

Dữ liệu nằm trong `runtime/credit.sqlite3` trên máy chủ (hoặc đường dẫn cấu hình
`CREDIT_DB_PATH`), vẫn còn sau khi khởi động lại. Hồ sơ cũ tự xuất hiện, không cần
nhập lại. Họ tên không được lưu trong bản ghi thẩm định; khi thẩm định lại cần nhập
họ tên. Lịch sử các lần thẩm định khác với lịch sử thanh toán: thông tin CIC vẫn
do người dùng nhập hoặc lấy từ mẫu, chưa có kết nối CIC tự động.

Loan Officer chỉ thấy hồ sơ mình khởi tạo, kể cả khi Risk Manager thẩm định lại.
Risk Manager và Committee Chair được xem các hồ sơ đã lưu. API mới:
`GET /cases?q=...&limit=20&offset=0` và
`GET /cases/{case_id}/history?limit=20&offset=0`; cả hai yêu cầu đăng nhập.

| Vai trò | Quyền |
|---|---|
| Loan Officer | Nhập/thẩm định hồ sơ ở ngưỡng chính thức, batch, xem lại hồ sơ mình đã thẩm định, đọc/xuất danh sách mẫu |
| Risk Manager | Thẩm định, chọn ngưỡng so sánh, phân tích độ nhạy, xem audit và kết quả đã lưu |
| Committee Chair | Thẩm định ở ngưỡng chính thức, xem kết quả/audit, ghi quyết định hội đồng và mô phỏng Core Banking |

Loan Officer chỉ đọc/ghi hồ sơ do mình khởi tạo. Risk Manager thẩm định lại không làm chuyển quyền này; chưa có quy trình chuyển giao chủ hồ sơ.

Quyền được kiểm tra tại server; không lấy `role` hoặc `officer_id` từ payload nghiệp vụ. Họ tên không lưu trong database nghiệp vụ; khi mở lại hồ sơ chỉ nạp các trường được phép lưu. Dữ liệu tài chính và nhân khẩu học còn lại vẫn là dữ liệu nhạy cảm cần phân quyền và chính sách lưu trữ.

## Luồng sử dụng

1. Đăng nhập, điền đầy đủ hồ sơ hoặc chọn hồ sơ tổng hợp từ **Danh sách mẫu**.
2. **Chạy thẩm định**. Server xác minh artifacts khi khởi động, chạy pipeline, hard rules, threshold và TreeSHAP. Khi mất kết nối, UI báo lỗi và không tự tạo xác suất.
3. UI hiển thị xác suất model và quyết định nghiệp vụ riêng biệt. SHAP gồm đầy đủ 54 đóng góp; biểu đồ gộp các yếu tố còn lại để giữ phép cộng chính xác.
4. Nếu sửa dữ liệu, kết quả trên UI mất hiệu lực. Yêu cầu trùng trong 10 giây trả cùng request ID; lần chạy mới được đánh số bền vững trong database.
5. Chủ tịch tra cứu mã hồ sơ, chọn quyết định và lưu. Server chỉ chấp nhận kết quả mới nhất trong 24 giờ, không ở tương lai và đúng phiên bản hiện hành. Người từng thẩm định cùng mã hồ sơ không được ghi quyết định hội đồng cho hồ sơ đó, kể cả sau khi người khác chạy lại. Phê duyệt phải dựa trên ngưỡng chính thức, không vi phạm hard rules, model đã duyệt và hạn mức không vượt số tiền đã thẩm định.
6. Quyết định đã lưu không phải chữ ký số bằng chứng thư. Mô phỏng Core Banking yêu cầu quyết định đã phê duyệt; mã giao dịch bắt đầu `SIM-`, trạng thái `SIMULATED_NOT_DISBURSED`. Không kết nối ngân hàng hoặc chuyển tiền.

Phân tích độ nhạy không thay đổi hồ sơ gốc hoặc audit chính thức. DTI điều chỉnh theo giảm thu nhập và hệ số giả định 5% cho mỗi điểm phần trăm tăng lãi suất. Model vẫn giữ công thức/giới hạn tiền xử lý đã huấn luyện; kết quả không được diễn giải thành PD, NPL, EL hay dự phòng pháp định.

## Lưu trữ và bảo vệ artifacts

- `models/`: 6 artifacts của release 1.2.0, không thay đổi. `reports/artifact_manifest.json` chứa SHA-256 chuẩn đã đối chiếu với audit trước sửa.
- Startup kiểm tra hash trước khi `joblib.load`. Sai hash hoặc thiếu artifact: không phục vụ thẩm định. Config threshold thiếu/sai: không tự hạ ngưỡng.
- Manifest là baseline integrity, **không phải chữ ký số**. Cần bảo vệ cả code, manifest và model bằng ACL/quyền filesystem hoặc image chỉ đọc.
- `runtime/credit.sqlite3`: tài khoản (mật khẩu PBKDF2), phiên có hạn 8 giờ, assessments, quyết định, mô phỏng và audit mới. Audit và nghiệp vụ commit trong cùng transaction. Trigger chặn UPDATE/DELETE trên các bảng assessments, committee, core_simulations và audit_events qua đường SQL thông thường; không thay thế kho WORM bên ngoài.
- `logs/audit.jsonl` và `.bak`: giữ nguyên dữ liệu lịch sử. API chỉ đọc bản đã ẩn nội dung tự do; **file cũ chưa bị tẩy/xóa PII**. Hạn chế quyền filesystem và xử lý theo chính sách retention được phê duyệt.
- Session cookie HttpOnly/SameSite=Strict, Secure khi HTTPS; giới hạn thử đăng nhập, chặn cross-origin cho thao tác ghi, giới hạn request 2 MB và batch 100 hồ sơ.
- UI không dùng CDN/font/script bên ngoài và không nội suy dữ liệu vào `innerHTML`.

SQLite phù hợp demo/pilot nội bộ với tải nhỏ. Inference được tuần tự hóa trong transaction để chống lặp giữa workers; chưa có benchmark tải lớn. Database vẫn là file cục bộ, cần volume bền vững, backup nhất quán và bảo vệ ổ đĩa. Không đặt file SQLite trên network share.

## API 1.3 — thay đổi so với giao diện cũ

Đăng nhập qua `POST /auth/login`, giữ cookie và gửi `X-Credit-Client: cockpit` khi POST. Các endpoint nghiệp vụ yêu cầu đăng nhập; không có API key hard-code. `/docs` là tài liệu cục bộ, mở sau khi đăng nhập cùng origin và không cần CDN. Dùng `/openapi.json` để tích hợp công cụ API.

- `GET /config`: constraints và ngưỡng từ backend; UI lấy vocabulary tại đây.
- `POST /predict`: mọi trường hồ sơ phải được gửi rõ ràng; không suy diễn hồ sơ từ `{}`. Trả `shap_base_value`, `fx_log_odds`, `prob_from_log_odds`, toàn bộ `shap_factors`, phiên bản và timestamp server.
- `POST /queue/batch-assess`: trả kết quả và danh sách `errors`; tổng hồ sơ luôn tính cả hồ sơ lỗi.
- `GET /cases/{case_id}/latest`: xem lần thẩm định mới nhất và quyết định đã lưu. Loan Officer chỉ xem lại hồ sơ mình thẩm định.
- `POST /audit/committee-decision`: nhận `assessment_id`, `idempotency_key`, `final_decision`, `approved_limit_vnd`, `interest_rate_pct`.
- `POST /integration/core-banking/disburse`: nhận `decision_id`, `account_number`, `idempotency_key`; chỉ mô phỏng.
- `/simulate-stress/portfolio`: trả số hồ sơ đạt/knockout trước/sau cú sốc và số chuyển tầng. Đã bỏ trường NPL/EL/dự phòng không có cơ sở.
- `/audit-logs?limit=100`: tối đa 500 bản ghi; chỉ Risk Manager/Committee Chair.

**Client cũ cần cập nhật** vì cơ chế đăng nhập và payload hội đồng/Core Banking đã thay đổi. Không dùng lại các script sửa source hoặc gọi live trong `scratch/`.

## Kiểm thử

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python -B -m pytest -p no:cacheprovider -s -q
```

Browser tests chỉ truy cập loopback, chặn external traffic. Test suite có database/log riêng trong thư mục tạm, kiểm tra hash models và logs trước/sau. Không chạy server đang phục vụ thật để test nghiệp vụ.

Dependencies trực tiếp được pin theo môi trường kiểm thử; chưa có lock toàn bộ dependency bắc cầu. Cảnh báo deprecation của SHAP/Starlette trong môi trường này không được che đi.

## Triển khai container

Dockerfile chỉ copy thành phần runtime; không đưa data, logs lịch sử, notebooks, scratch hay cloudflared vào image. Model được đặt không ghi được bởi appuser. Gắn volume riêng vào `/app/runtime`; không thay volume này giữa CLI tạo tài khoản và server.

Biến môi trường:

| Biến | Mặc định / ý nghĩa |
|---|---|
| `CREDIT_DB_PATH` | `runtime/credit.sqlite3` theo root project |
| `CREDIT_ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver`; đặt hostname thật khi triển khai |
| `AUDIT_LOG_DIR` | Thư mục legacy JSONL; API mới lưu transactional audit trong SQLite |

Đưa lên mạng cần HTTPS reverse proxy được cấu hình đúng forwarded headers và hostname. `share_link.bat` không tự mở public tunnel. Chưa build/deploy container trong lượt sửa này.

## Nghiên cứu và các giới hạn được giữ nguyên

Các báo cáo/model card cũ ghi nhận kết quả nghiên cứu 1.2.0, không phải chứng nhận ứng dụng hiện tại sẵn sàng production. Inference kiểm chứng: test AUC 0,920747, cost 282 ở ngưỡng 0,73.

Không retrain trong đợt sửa. Đã sửa source CV để preprocessor được fit trong từng fold ở lần nghiên cứu sau; chưa có benchmark mới. Script train/preprocessing từ chối ghi đè thư mục release mặc định và yêu cầu thư mục thí nghiệm riêng.

Để giữ tương thích model, không sửa các phép biến đổi đã được huấn luyện: nhóm tuổi 18, kỳ hạn dưới 12 tháng, median phụ thuộc batch và lãi suất tham chiếu cố định. Đây là các hạn chế phải đánh giá trong một phiên bản model mới, không được âm thầm thay công thức trong inference 1.2.0.
