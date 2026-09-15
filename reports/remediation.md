# Kết quả sửa và kiểm chứng ứng dụng 1.3.0

## Phạm vi thực hiện

Đã sửa ứng dụng phục vụ và quy trình nghiệp vụ; không retrain, không chạy tuning, không gọi AI/API ngân hàng bên ngoài, không commit/push. Model XGBoost 1.2.0 và cấu hình threshold giữ nguyên hash từ audit ban đầu. Không tìm thấy Independent AI Supervisor trong source ban đầu; ứng dụng hoàn thiện không tích hợp thành phần này.

## Thay đổi chính

- Một Decision Engine phục vụ inference; API dùng chung model trong bộ nhớ. Startup kiểm tra cả 6 artifacts trước giải tuần tự hóa; config lỗi không fallback sang ngưỡng khác.
- UI HTML/CSS/JS mới dùng tài nguyên cục bộ, loại bỏ các bộ simulator và số liệu giả khi offline. Hai trang HTML dùng chung JavaScript/CSS, không có quyết định riêng.
- SHAP trả đủ 54 đóng góp với độ chính xác đầy đủ, giá trị nền, margin và xác suất. Waterfall gộp phần còn lại thay vì bỏ mất đóng góp.
- Đăng nhập PBKDF2 và cookie HttpOnly; RBAC server, chặn cross-origin POST, hạn chế body/batch/login. Không có user/password mặc định hoặc API key hard-code.
- SQLite lưu assessments, số run, idempotency, quyết định hội đồng, mô phỏng Core Banking và audit. Nghiệp vụ và audit commit/rollback cùng transaction.
- Phê duyệt phải tham chiếu lần thẩm định mới nhất trong 24 giờ, ở ngưỡng chính thức; không được vượt hard rules/model rejection/hạn mức đã thẩm định. Chặn quyết định trùng và mô phỏng trùng.
- Core Banking phản hồi SIMULATED_NOT_DISBURSED, mã SIM; không giả mạo giao dịch ngân hàng hoặc chữ ký số.
- Giảm thiểu PII: không lưu tên hoặc tài khoản đầy đủ trong database/audit mới. Schema loại bỏ payload tự do; UI dùng textContent thay innerHTML; lỗi validation không trả giá trị nhập.
- Log cũ được giữ nguyên; API ẩn nội dung tự do khi đọc lịch sử. Dữ liệu tài chính/nhân khẩu học được lưu theo allowlist vẫn cần bảo vệ riêng.
- Batch trả danh sách lỗi rõ ràng. Stress không ghi audit thẩm định, dùng cùng engine và trả quyết định thật; sửa chuyển tầng, bỏ suy diễn PD/NPL/EL/dự phòng.
- Cập nhật hướng dẫn tài khoản, API, triển khai; pin dependencies trực tiếp; Docker chỉ đóng gói runtime và để model không ghi được bởi appuser.
- Source nghiên cứu CV chuyển preprocessing vào từng fold. Chưa huấn luyện hoặc tạo benchmark mới. Script train/preprocessing không cho ghi đè thư mục release mặc định.

## Kiểm chứng

Lệnh:

```powershell
python -B -m pytest -p no:cacheprovider -s -q
```

Kết quả: **66 passed, 4 warnings**, khoảng 81 giây trên môi trường Python 3.13 hiện có.

Bao gồm:

- Bộ regression hiện có về model, data splits, preprocessing, hard rules, vocabulary, fairness và inference consistency.
- Auth, RBAC, giả mạo role, cross-origin, session expiry/revocation, rate limit, body limit.
- PII thật trong snapshot đầu vào, phản chiếu lỗi validation, đầy đủ phép cộng SHAP.
- Gọi đồng thời tạo một run, restart/reopen giữ dữ liệu, idempotency conflict, rollback khi ghi event lỗi, audit chặn UPDATE/DELETE.
- Quyết định cũ, knockout, ngưỡng so sánh không được phê duyệt; mô phỏng chỉ nhận quyết định hợp lệ.
- Browser Chromium: đăng nhập theo vai trò, 54 SHAP, XSS sentinel được giữ như văn bản, tra cứu/quyết định/mô phỏng, thay đổi hồ sơ làm mất hiệu lực kết quả, mất mạng không tạo kết quả, không request ra bên ngoài.
- Desktop 1440 px và mobile 390 px; không có tràn chiều ngang ở màn hình mobile đã kiểm tra. Ảnh tại `reports/ui_verification/` chứa dữ liệu test, bao gồm XSS sentinel có chủ đích.
- SHA-256 models và production logs trước/sau full suite giống nhau. Hash artifacts cũng khớp manifest của audit ban đầu.

4 cảnh báo còn lại: 3 deprecation của SHAP/Matplotlib và 1 deprecation Starlette TestClient/httpx. Môi trường máy có thêm cảnh báo tương thích requests ở lúc khởi động pytest; không thuộc dependency runtime mới. Không thay đổi thư viện toàn máy để che cảnh báo.

## Giới hạn còn lại được công khai

- Không thể cam kết phần mềm hoàn hảo hoặc đã đạt chuẩn production từ một lượt test. Chưa chạy Docker build, load test lớn, penetration test độc lập hoặc deploy.
- Database cục bộ chưa mã hóa ở tầng ứng dụng. Cần ACL, mã hóa ổ đĩa, backup nhất quán, retention và HTTPS khi dùng dữ liệu thực. Trigger/manifest không thay thế WORM/chữ ký số.
- Log lịch sử vẫn chứa PII trên filesystem; không xóa/sửa bằng đợt sửa này. Chỉ luồng đọc qua API được hạn chế/ẩn dữ liệu tự do.
- Model huấn luyện trên dữ liệu tổng hợp, không phải mô hình PD. Các báo cáo cũ là kết quả nghiên cứu lịch sử.
- Các phép biến đổi tuổi 18, kỳ hạn dưới 12 tháng, median theo batch và lãi suất tham chiếu cố định được giữ nguyên vì thuộc hợp đồng inference của model đóng băng. Cần một phiên bản model mới để sửa và tái kiểm định; không thay âm thầm.
- Ngưỡng, hard rules và xác suất model không đổi. RBAC và điều kiện ghi quyết định là lớp kiểm soát mới ở bên ngoài Decision Engine.
- Dependencies bắc cầu chưa có lock toàn bộ; các phiên bản trực tiếp đã được pin theo môi trường kiểm thử.

## Bắt đầu sử dụng

Quản trị viên phải tạo tài khoản bằng `python -m src.auth <username> --role "Loan Officer"` (hoặc vai trò phù hợp), nhập mật khẩu riêng, rồi chạy `run_server.bat`. Xem README.md để tạo đủ các vai trò và triển khai an toàn. Chưa tạo tài khoản/mật khẩu vận hành thay người dùng.
