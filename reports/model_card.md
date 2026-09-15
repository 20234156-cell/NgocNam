# MODEL CARD: HỆ THỐNG DỰ ĐOÁN PHÊ DUYỆT KHOẢN VAY TÍN DỤNG (VIỆT NAM)
## Vietnamese Loan Approval Prediction System - Model Card (Version 1.2.0)

Tài liệu thẻ mô hình (Model Card) chuẩn hóa theo thông lệ quốc tế và ngành ngân hàng / FinTech để quản trị rủi ro mô hình (Model Risk Management - MRM).

---

## 1. Thông Tin Tổng Quan Về Mô Hình (Model Details)
- **Tên mô hình:** Vietnamese Credit Underwriting XGBoost Classifier
- **Phiên bản:** `1.2.0` (Cập nhật: Tháng 09/2026 - Chuẩn hóa Vocabulary, Audit Trail, Single-Source of Truth)
- **Thuật toán cốt lõi:** Gradient Boosted Decision Trees (XGBoost) kết hợp Pipeline tiền xử lý Scikit-Learn.
- **Tối ưu siêu tham số:** Bayesian Optimization qua Optuna (30 trials trên Stratified 5-Fold Cross Validation).
- **Lớp giải thích mô hình:** TreeSHAP (Shapley Additive exPlanations) suy luận thời gian thực.
- **Bộ não nghiệp vụ:** Decision Engine tập trung (`src/decision.py`) điều phối Hard Rules, Risk Tiering, và Recommendations.
- **Ngôn ngữ & Môi trường:** Python 3.13, Scikit-Learn 1.6+, XGBoost 3.4+, SHAP 0.52+, FastAPI 0.110+, Streamlit 1.61+.

---

## 2. Mục Đích Sử Dụng (Intended Use)
### Mục đích chính:
- Hệ thống hỗ trợ ra quyết định thử nghiệm (Proof of Concept - PoC / Decision Support System - DSS) nhằm minh họa và nghiên cứu giải pháp AI minh bạch (Explainable AI) trong thẩm định tín dụng bán lẻ tại Việt Nam.
- Cung cấp lý do minh bạch (Top 3-5 nhân tố SHAP) khi từ chối hoặc phê duyệt khoản vay nhằm hỗ trợ cán bộ tín dụng giải trình.

### Các trường hợp KHÔNG khuyến nghị sử dụng (Out-of-Scope / Non-goals):
- **Triển khai tự động phê duyệt trực tiếp (Production Credit Approval):** Mô hình chưa qua kiểm định trên dữ liệu lịch sử vỡ nợ (Default / PD) thật của ngân hàng thương mại.
- **Khoản vay doanh nghiệp lớn:** Mô hình thiết kế riêng cho khách hàng cá nhân (Retail Banking).
- **Quyết định tự động 100% không có sự can thiệp của con người:** Cán bộ tín dụng có thẩm quyền phải kiểm tra thực địa tài sản và hồ sơ pháp lý trước khi giải ngân.

---

## 3. Dữ Liệu Huấn Luyện & Kiểm Thử (Data Summary)
- **Tổng số hồ sơ:** 6,000 hồ sơ khách hàng Việt Nam độc lập.
- **Phân chia dữ liệu:**
  - Tập huấn luyện (Train): 4,200 mẫu (70%)
  - Tập kiểm định (Validation): 900 mẫu (15%) - Dùng tune hyperparameter và tối ưu ngưỡng chi phí rủi ro ngân hàng.
  - Tập kiểm thử độc lập (Test): 900 mẫu (15%) - Kiểm tra mù (Blind Test) hoàn toàn leak-free.
- **Đặc điểm dữ liệu:**
  - Tiền tệ: Việt Nam Đồng (VNĐ).
  - Chuẩn đánh giá tín dụng: Điểm tín dụng CIC (400 - 850), Phân nhóm nợ CIC (Nhóm 1 đến Nhóm 5) theo quy định của Ngân hàng Nhà nước Việt Nam.
  - Tổng số đặc trưng sau feature engineering và mã hóa: 54 đặc trưng.

---

## 4. Hiệu Năng Mô Hình Thực Tế Trên Tập Test (Performance)
Kết quả đánh giá trên tập Test độc lập (900 hồ sơ chưa từng xuất hiện trong quá trình train và tune threshold):

| Chỉ số đánh giá | Giá trị thực tế | Nhận định chuyên môn |
| :--- | :---: | :--- |
| **ROC-AUC** | **0.9207** | Khả năng phân biệt giữa hồ sơ rủi ro và an toàn rất cao trên không gian dữ liệu mô phỏng |
| **PR-AUC (Average Precision)** | **0.9141** | Độ tin cậy cao trên toàn dải ngưỡng |
| **Accuracy (Độ chính xác)** | **83.22%** | Tỷ lệ dự đoán đúng trên toàn bộ tập test |
| **Recall (Độ phủ lớp phê duyệt)** | **85.01%** | Nhận diện được 85% khách hàng đủ điều kiện vay |
| **Precision (Độ chuẩn xác)** | **81.90%** | 82% khách hàng mô hình duyệt là người vay tốt |
| **F1-Score** | **0.8342** | Cân bằng hài hòa giữa Precision và Recall |
| **Brier Score** | **0.1132** | Xác suất dự đoán có độ hiệu chuẩn (calibration) cao |

### Tối ưu hóa Ngưỡng theo Chi phí Rủi ro Ngân hàng (Leak-Free):
- Ngưỡng mặc định: `0.50` (Chi phí rủi ro trên Test: 403)
- Ngưỡng tối ưu chi phí khóa từ tập Validation (`Cost = 4*FP + 1*FN`): **`0.73`**
- Đánh giá mù trên Test: Chi phí rủi ro giảm xuống **282**; số lượng False Positive giảm từ 84 xuống 31 (tương đương giảm 63.1% số ca FP trên tập Test tại ngưỡng 0.73, giúp hạn chế tỷ lệ hồ sơ không đạt chuẩn bị phân loại nhầm là đủ điều kiện cấp tín dụng).

---

## 5. Giải Thích Quyết Định & Nhân Tố Then Chốt (Explainability)
Xếp hạng các yếu tố ảnh hưởng mạnh nhất đến việc phê duyệt khoản vay qua SHAP:
1. **`diem_tin_dung_cic` (Điểm CIC):** Khách hàng có điểm CIC > 700 đóng góp điểm cộng lớn nhất.
2. **`so_lan_tre_han_2_nam` (Lịch sử trễ hạn):** Tác động tiêu cực mạnh nhất khi trễ hạn >= 2 lần.
3. **`nhom_no_cic` (Phân nhóm nợ CIC):** Rơi vào Nhóm 3-5 bị loại trừ tức thì (Hard policy knockout).
4. **`ty_le_dti` (Tỷ lệ Nợ/Thu nhập):** Tác động tiêu cực khi vượt ngưỡng an toàn 45%.
5. **`ty_le_vay_tren_tai_san_ltv` (Hệ số LTV):** Tài sản đảm bảo giá trị cao làm tăng điểm uy tín.

---

## 6. Đánh Giá Tính Công Bằng & Đạo Đức AI (Fairness & Ethics)

> [!WARNING]
> **Khuyến cáo học thuật về Giới hạn Kiểm toán Công bằng (Methodological Disclaimer):**
> Các chỉ số **Disparate Impact Ratio (DIR)** và **Equal Opportunity Difference (EOD)** được sử dụng như công cụ định lượng nhằm phát hiện dấu hiệu chênh lệch thống kê giữa các phân khúc dân số trên tập dữ liệu thử nghiệm; **kết quả này không thay thế một cuộc kiểm toán công bằng và đạo đức tín dụng toàn diện (Fair Lending Audit)**.
> Đặc biệt, do bản chất của tập dữ liệu là **dữ liệu mô phỏng (Synthetic Data)**, kết quả Fairness Audit ở đây chỉ nên được trình bày như **một thí nghiệm phương pháp luận**, không phải bằng chứng khẳng định rằng một hệ thống thẩm định tín dụng thực tế là hoàn toàn công bằng hay không có thiên kiến.

### 6.1. Bảng Kiểm Toán Đa Chiều Tại Ngưỡng Tối Ưu Chi Phí Đã Khóa (0.73)
Kiểm định trên tập kiểm thử độc lập (Test Set, N = 900 hồ sơ) qua 3 lát cắt nhân khẩu học chính:

| Lát cắt nhân khẩu học | Nhóm đối chứng (Unprivileged) | Nhóm ưu tiên (Privileged) | Tỷ lệ duyệt đối chứng (%) | Tỷ lệ duyệt ưu tiên (%) | DIR (Tỷ lệ tác động khác biệt) | EOD (Chênh lệch cơ hội bình đẳng) | Đánh giá sơ bộ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Giới tính** | Nữ (N=433) | Nam (N=467) | 33.95% | 37.04% | **0.9164** | **-0.0229** | Đạt chuẩn tham chiếu (DIR $\ge$ 0.80, \|EOD\| $\le$ 0.10) |
| **Độ tuổi** | Dưới 30 tuổi (N=173) | Từ 30 tuổi trở lên (N=727) | 32.37% | 36.31% | **0.8914** | **+0.0126** | Đạt chuẩn tham chiếu (DIR $\ge$ 0.80, \|EOD\| $\le$ 0.10) |
| **Khu vực cư trú** | Ngoại thành / Nông thôn (N=436) | Nội thành / Đô thị (N=464) | 36.01% | 35.13% | **1.0250** | **+0.0005** | Đạt chuẩn tham chiếu (DIR $\ge$ 0.80, \|EOD\| $\le$ 0.10) |

### 6.2. Đối Chiếu Chuyển Đổi Giữa Ngưỡng Mặc Định (0.50) và Ngưỡng Khóa (0.73)
| Lát cắt | DIR (Ngưỡng 0.50) | DIR (Ngưỡng 0.73) | EOD (Ngưỡng 0.50) | EOD (Ngưỡng 0.73) | Nhận xét xu hướng kỹ thuật |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Giới tính** | 0.8840 | **0.9164** | -0.0655 | **-0.0229** | DIR tiệm cận 1.0; khoảng cách tỷ lệ nhận diện đúng (TPR) giữa Nam và Nữ thu hẹp chỉ còn 2.29% |
| **Độ tuổi** | 0.8492 | **0.8914** | -0.0425 | **+0.0126** | Thu hẹp khoảng cách chấp thuận; TPR giữa nhóm trẻ và nhóm trưởng thành gần như cân bằng hoàn toàn (65.71% vs 64.46%) |
| **Khu vực cư trú** | 1.0370 | **1.0250** | +0.0150 | **+0.0005** | Không phát hiện dấu hiệu phân biệt địa lý |

### 6.3. Nguyên Tắc Bảo Vệ & Quản Trị Đạo Đức AI
- **Giám sát biến nhạy cảm:** Biến giới tính (`gioi_tinh`) và tình trạng hôn nhân (`tinh_trang_hon_nhan`) có tham gia làm đặc trưng đầu vào mô hình, nhưng được giám sát chặt chẽ qua kiểm toán DIR/EOD (xem Mục 6.1) — đảm bảo không có thiên kiến phân biệt vượt ngưỡng chuẩn tham chiếu. Các biến này không được sử dụng làm nhân tố xét duyệt đơn phương hay định giá lãi suất trực tiếp.
- **Giảm thiểu PII:** Các biến định danh (`ho_ten`, `ma_ho_so`) bị loại bỏ hoàn toàn khỏi ma trận đặc trưng mô hình và không được ghi vào nhật ký kiểm toán.
- **Quyền được giải trình:** Tích hợp mô hình SHAP giải thích định lượng trên từng hồ sơ để cung cấp cơ sở từ chối/chấp thuận minh bạch.


---

## 7. Giới Hạn & Cảnh Báo Vận Hành (Limitations & Warnings)
> [!IMPORTANT]
> **Giới hạn về bản chất Dữ liệu Tổng hợp (Synthetic Circularity):**
> Bộ dữ liệu hiện tại được sinh mô phỏng dựa trên các quy luật thống kê và giả định nghiệp vụ ngân hàng. Nhãn mục tiêu được tạo ra từ tổ hợp các chỉ số tín dụng (CIC, DTI, LTI, LTV...), do đó chỉ số ROC-AUC ~0.92 phản ánh năng lực của mô hình trong việc xấp xỉ lại các quy luật được lập trình trong dữ liệu tổng hợp. Đây là kết quả có giá trị trong khuôn khổ nghiên cứu phương pháp luận và demo kiến trúc hệ thống, nhưng **không được suy diễn tương đương với hiệu năng trên dữ liệu hành vi tín dụng thực tế**.
>
> **Khuyến nghị:** Trước khi đưa vào môi trường sản xuất thực tế, bắt buộc phải huấn luyện và kiểm định lại toàn bộ hệ thống trên dữ liệu lịch sử vỡ nợ (Default / PD) thật của tổ chức tín dụng.

---

## 8. Quản Trị Vết Kiểm Toán & Quyền Riêng Tư (Audit Trail & PII Minimization)
- **Bản chất dữ liệu Demo:** Tên khách hàng (`ho_ten`) và mã hồ sơ (`ma_ho_so`) xuất hiện trên giao diện Streamlit và API chỉ mang tính chất minh họa kịch bản sử dụng (Demo Data).
- **Nguyên tắc Giảm thiểu Dữ liệu (PII Minimization):** Hệ thống tuân thủ nghiêm ngặt bảo vệ quyền riêng tư: **Tuyệt đối không lưu trữ `ho_ten`, số điện thoại, CCCD hay dữ liệu cá nhân nhạy cảm vào `logs/audit.jsonl`**.
- **Cấu trúc dữ liệu Vết Kiểm Toán Tối Thiểu (Minimum Audit Schema):**
  - `timestamp`: Thời điểm thẩm định theo chuẩn UTC ISO 8601.
  - `request_id`: Mã định danh giao dịch duy nhất (UUID) cho mỗi lần thẩm định.
  - `ma_ho_so`: Mã hồ sơ tín dụng tham chiếu.
  - `model_version`: Phiên bản mô hình AI (`1.1.0`).
  - `threshold_config_version`: Phiên bản cấu hình ngưỡng chi phí áp dụng (`1.1.0`).
  - `decision_engine_version`: Phiên bản bộ quy tắc và logic ra quyết định (`1.1.0`).
  - `prob_approved`: Xác suất phê duyệt do mô hình dự đoán.
  - `threshold`: Ngưỡng quyết định áp dụng tại thời điểm xét duyệt.
  - `decision`: Kết quả phê duyệt / từ chối cuối cùng.
  - `risk_tier`: Phân tầng mức độ rủi ro tín dụng.
  - `hard_rule_violated`: Trạng thái vi phạm quy tắc chính sách tín dụng cứng.
  - `recommendation`: Khuyến nghị nghiệp vụ hành động được cho cán bộ tín dụng.
  - `top_shap_factors`: Top nhân tố định lượng đóng góp theo SHAP.
- **Giá trị về Khả năng Tái Hiện & Truy Nguyên Nguồn Gốc (Reproducibility & Lineage):**
  Lưu trữ đầy đủ `request_id`, `model_version`, `threshold_config_version`, và `decision_engine_version` cho phép trả lời câu hỏi cốt lõi trong thanh tra ngân hàng:
  *“Tại thời điểm hồ sơ này được xét, hệ thống đang dùng mô hình và bộ quy tắc nào?”*
- **Kiến trúc Luồng Dữ Liệu Tập Trung (Unified Architecture):**
  Cả Streamlit UI và FastAPI đều bắt buộc đi qua cùng một điểm điều phối duy nhất (`DecisionEngine`):
  `Streamlit UI / FastAPI -> DecisionEngine -> (Prediction, Business Rules, SHAP) -> AuditLogger -> logs/audit.jsonl`.
  Không tạo logger riêng rẽ hay phân mảnh logic giữa các kênh tiếp nhận.
