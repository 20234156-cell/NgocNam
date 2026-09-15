# Đối chiếu đề bài và rà soát logic — 15/09/2026

## 1. Kết luận và phạm vi nghiệm thu

Đề bài: **Xây dựng chương trình dự đoán khả năng được phê duyệt khoản vay dựa trên thông tin tài chính và lịch sử tín dụng của khách hàng.**

Dự án đáp ứng chức năng cốt lõi của đề bài dưới dạng hệ thống hỗ trợ thẩm định (DSS) trên dữ liệu tổng hợp. Không đồng nghĩa đã được ngân hàng chấp thuận vận hành, đã kiểm chứng trên khách hàng thật hoặc không còn lỗi. Không có kết nối chuyển tiền thực.

| Yêu cầu | Triển khai hiện tại | Giới hạn |
|---|---|---|
| Thông tin tài chính | Thu nhập chính/đồng vay, tài sản, số tiền, kỳ hạn, DTI | Người dùng khai báo; chưa đối soát chứng từ hoặc tính DTI từ lịch trả nợ thực |
| Lịch sử tín dụng | Điểm CIC, nhóm nợ, chậm trả, hợp đồng đang mở, tiền sử nợ xấu | Chưa kết nối CIC; không xác thực nguồn dữ liệu |
| Dự đoán | Pipeline XGBoost-CreditRisk-v1.2.0, 54 đặc trưng | Nhãn phê duyệt sinh theo giả định, không phải quan sát phê duyệt/vỡ nợ thực |
| Quyết định rõ ràng | Decision Engine tập trung, hard rules ưu tiên, ngưỡng chính thức 0,73 | Chính sách demo; chưa có phê chuẩn của ngân hàng |
| Giải thích | TreeSHAP đầy đủ, đóng góp trong miền log-odds | Giải thích hành vi model, không chứng minh nhân quả hoặc khả năng trả nợ |
| Giao diện | HTML/CSS/JS, tiền bằng số và chữ, báo lỗi, vô hiệu hóa kết quả khi sửa | Không có Streamlit trong luồng chạy hiện tại |
| API/quy trình | FastAPI, đăng nhập, ba vai trò, lưu kết quả và quyết định | Chưa có IAM/MFA doanh nghiệp, chữ ký số, quy trình bàn giao hồ sơ |
| Kiểm toán | SQLite, giao dịch nguyên tử, idempotency, ghi nối tiếp | Không phải WORM; quản trị viên filesystem vẫn có thể thay DB/code |

## 2. Logic xử lý thực tế

1. Xác thực phiên và quyền. API kiểm tra dữ liệu bắt buộc, vocabulary, phạm vi và kích thước yêu cầu.
2. Kiểm tra chủ hồ sơ: Loan Officer chỉ đọc/ghi mã hồ sơ do mình khởi tạo. Risk Manager có thể thẩm định lại nhưng không chuyển quyền chủ hồ sơ.
3. Pipeline đóng băng biến đổi dữ liệu và XGBoost tính xác suất nhãn phê duyệt. Tên và mã hồ sơ không phải đặc trưng model.
4. Decision Engine áp dụng quy tắc: nhóm nợ 3–5, CIC dưới 450, hoặc tiền sử nợ xấu kèm CIC dưới 540 dẫn tới từ chối. Nếu không vi phạm, áp dụng ngưỡng 0,73; ngưỡng 0,50 chỉ dùng so sánh bởi Risk Manager. Không bổ sung chính sách tín dụng mới trong đợt này.
5. SHAP giải thích điểm model. Xác suất cao vẫn có thể bị hard rules từ chối; đó không phải hai quyết định mâu thuẫn. Các mức rủi ro theo điểm phê duyệt không phải xếp hạng PD đã hiệu chuẩn.
6. Kiểm tra giá trị hữu hạn, phạm vi xác suất, tổng SHAP/margin, sigmoid và xác suất hiển thị. Nếu không nhất quán, trả lỗi 503 và không lưu thẩm định/audit thành công.
7. Lưu kết quả và audit trong cùng transaction. Yêu cầu trùng cùng người/nội dung trong 10 giây có thể trả kết quả cũ, không tạo run trùng.
8. Hội đồng chỉ ghi quyết định với kết quả mới nhất, tuổi kết quả từ 0 đến 24 giờ và cùng phiên bản model/config/engine. Người từng tạo bất kỳ lần thẩm định nào của cùng mã hồ sơ không được ghi quyết định hội đồng cho mã đó. Cần tài khoản chủ tịch khác nếu chủ tịch đã tự thẩm định.
9. Phê duyệt còn yêu cầu kết quả đạt chính sách/ngưỡng chính thức và hạn mức dương không vượt khoản vay đã thẩm định. Điều khoản lãi suất chỉ được ghi nhận, không tái tính model. Không coi đây là đánh giá đủ khả năng trả nợ với hợp đồng thực.
10. Core chỉ ghi mô phỏng cho quyết định hợp lệ; không chuyển tiền. Replay cùng idempotency key/nội dung trả giao dịch đã ghi, không phải phê duyệt mới hoặc chuyển tiền lần nữa.

Ngưỡng so sánh qua `/predict` vẫn tạo một lần thẩm định mới, vì vậy có thể làm kết quả chính thức trước đó hết hiệu lực. Phải chạy lại ở ngưỡng chính thức trước khi phê duyệt. Stress test không ghi đè kết quả chính thức.

## 3. Những lỗi đã sửa thêm

- Chặn Loan Officer ghi tiếp vào mã hồ sơ của người khác; giữ quyền chủ hồ sơ khi Risk Manager thẩm định lại.
- Chặn người lập tự ghi quyết định hội đồng, kể cả qua một lần thẩm định trung gian do người khác lập.
- Tính mốc chống trùng sau khi lấy khóa transaction; không nhận cache với thời gian âm.
- Chặn kết quả tương lai, hết hạn hoặc khác phiên bản ở bước hội đồng và mô phỏng mới.
- Dừng và rollback nếu kết quả SHAP/xác suất không nhất quán.
- Bổ sung trigger chặn UPDATE/DELETE cho assessments, committee, core_simulations. Sửa hồ sơ bằng run mới, không sửa bản ghi lịch sử. Trigger được cài khi ứng dụng mở kết nối sau cập nhật; đợt kiểm thử chỉ dùng DB tạm, không mở DB vận hành.
- Đồng bộ giới hạn tạo tài khoản với login: tên không trống/không có khoảng trắng hai đầu, mật khẩu 12–256 ký tự.
- Bổ sung hướng dẫn tách người lập/người duyệt trên UI và README.

## 4. Diễn giải đúng kết quả mô hình

Đối chiếu đã thực hiện trước đợt bổ sung kiểm soát: 6.000 hồ sơ tổng hợp; train/validation/test = 4.200/900/900; test AUC khoảng 0,9207. Tại ngưỡng 0,73: TN=422, FP=31, FN=158, TP=289; accuracy 79%, chi phí giả định `4*FP+FN=282`. Các số này là đánh giá phân loại model trên nhãn tổng hợp, không phải tỷ lệ tổn thất tài sản hoặc đánh giá toàn bộ quy trình hội đồng.

FP ở đây là dự đoán duyệt trong khi nhãn tổng hợp là từ chối, **không phải khoản vay đã vỡ nợ**. AUC không chứng minh xác suất đã hiệu chuẩn cho khách hàng thật; hệ số chi phí 4:1 không phải đơn vị tiền. Không thể cam kết độ chính xác 100% hoặc không có tổn thất.

Các báo cáo lịch sử có nhắc Streamlit, “leak-free”, độ ổn định CV và hiệu chuẩn cần đọc cùng giới hạn hiện tại. Source CV đã được sửa để fit preprocessing trong từng fold cho nghiên cứu sau, nhưng chưa chạy lại huấn luyện/benchmark. Không dùng các nhận xét lịch sử đó làm chứng nhận độc lập cho release này. XGBoost cũng không vượt Logistic Regression về mọi metric trong bảng lịch sử; chưa có căn cứ gọi là model tốt nhất cho ngân hàng thật.

## 5. Rủi ro còn lại và kế hoạch trước vận hành thực

1. **Dữ liệu và mục tiêu:** thu thập dữ liệu được phép sử dụng, xác định dự đoán phê duyệt hay vỡ nợ, kiểm chứng nhãn, đánh giá theo thời gian và tập khách hàng ngoài mẫu. Không đổi ý nghĩa nhãn bằng cách đổi tên trên UI.
2. **Khả năng trả nợ:** xác minh thu nhập, CIC và tài sản; tính lịch trả nợ/DTI từ nghĩa vụ thực, lãi suất, phí và kỳ hạn. Cần chính sách được ngân hàng duyệt trước khi biến các chỉ tiêu thành hard rules.
3. **Release model mới:** xử lý nhóm tuổi 18, kỳ hạn dưới 12 tháng, median phụ thuộc batch, winsorization và lãi suất tham chiếu cố định 8,5%; kiểm định lại trước khi thay thế. Không âm thầm đổi preprocessing của model đóng băng.
4. **Rủi ro mô hình:** calibration, fairness theo nhóm (model có giới tính/tuổi và thông tin nhân khẩu), drift, dữ liệu ngoài phân phối, backtest, stress có căn cứ, kiểm định độc lập và cơ chế dừng/rollback.
5. **Kiểm soát nghiệp vụ:** xác thực danh tính khách hàng và chủ hồ sơ, bàn giao hồ sơ có audit, phát hiện hồ sơ trùng với mã khác, danh tính nhân viên riêng biệt. Tách tài khoản trong ứng dụng chưa chứng minh hai tài khoản thuộc hai người khác nhau.
6. **Bảo mật/vận hành:** TLS, MFA/IAM, quản lý secrets, mã hóa và retention, audit chống sửa ngoài máy ứng dụng, backup/khôi phục đã thử, quản lý thời gian máy chủ, kiểm thử tải và sự cố. SQLite đang tuần tự hóa inference, chưa chứng minh đáp ứng SLA ngân hàng.
7. **PII lịch sử:** file logs cũ có thể còn dữ liệu nhận diện; API đã giảm lộ dữ liệu nhưng không tẩy file gốc. Cần chính sách xử lý được phê duyệt. Không chỉnh logs hoặc runtime DB trong đợt này.
8. **Tích hợp ngân hàng:** cần xác minh người thụ hưởng, hệ thống sổ cái, hạn mức, đối soát, ký số và kiểm soát giao dịch thực; endpoint hiện tại chỉ là mô phỏng.

## 6. File liên quan và kiểm chứng

- `api/main.py`, `api/schemas.py`: API, xác thực và hợp đồng dữ liệu.
- `src/workflow.py`, `src/storage.py`, `src/auth.py`: kiểm soát quy trình, lưu trữ và tài khoản.
- `src/decision.py`, `src/preprocessing.py`, `src/feature_engineering.py`, `src/explainability.py`: suy luận/chính sách/giải thích hiện hành; không đổi trong đợt bổ sung này.
- `models/`, `reports/artifact_manifest.json`: artifacts đóng băng và baseline hash; không đổi.
- `app/cockpit.html`, `app/index.html`, `app/cockpit.js`, `app/styles.css`: UI.
- `tests/test_workflow_security.py`: hồi quy bảo mật và các ca biên mới; `tests/test_browser.py`: luồng browser thật, chặn mạng ngoài.
- `README.md`: cài đặt, tài khoản, chạy và giới hạn triển khai.

Kết quả kiểm thử ngày 15/09/2026: **78 passed, 4 warnings trong 135,76 giây**, gồm hai kiểm thử Chromium. Lệnh: `python -B -m pytest -p no:cacheprovider -s -q`. Có 12 ca kiểm thử bổ sung so với bộ 66 ca trước đó. Kiểm tra cú pháp Python và hai HTML shell giống nhau đạt; cả 6 hash artifact khớp manifest.

Bốn cảnh báo là deprecation của Starlette/httpx và SHAP/Matplotlib; môi trường Python toàn cục còn báo RequestsDependencyWarning lúc khởi động pytest. Chưa nâng dependency trong đợt này. Kiểm thử dùng DB/log tạm, kiểm tra hash models/logs trước và sau; không retrain, không đổi threshold/artifacts, không gọi API bên ngoài hoặc commit/push. Không khởi động lại server người dùng đang chạy; cần khởi động lại để nạp code mới.
