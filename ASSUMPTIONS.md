# TÀI LIỆU CÁC GIẢ ĐỊNH DỰ ÁN (ASSUMPTIONS.MD)
## Hệ thống Dự đoán Khả năng Phê duyệt Khoản vay (Loan Approval Prediction System)

Tài liệu này ghi lại toàn bộ các giả định về nghiệp vụ, dữ liệu và kỹ thuật được áp dụng trong quá trình phát triển hệ thống.

---

### 1. Giả định về Nguồn dữ liệu (Data Source Assumption)
- **Yêu cầu cụ thể từ người dùng:** Hệ thống phục vụ hoàn toàn đối tượng khách hàng Việt Nam, sử dụng ngôn ngữ Tiếng Việt cho toàn bộ dữ liệu, hồ sơ khách hàng, phân loại và các chỉ số thẩm định tín dụng.
- **Giải pháp áp dụng:** Tạo bộ dữ liệu mô phỏng tín dụng chuẩn Việt Nam gồm 6,000 bản ghi khách hàng (`data/raw/loan_data.csv`) với các trường thông tin:
  - Thông tin định danh: Mã hồ sơ (`ma_ho_so`), Họ tên người Việt (`ho_ten`), Tuổi, Giới tính, Tình trạng hôn nhân, Số người phụ thuộc, Học vấn, Nghề nghiệp.
  - Thông tin tài chính bằng VNĐ: Thu nhập tháng (`thu_nhap_thang_vnd`), Thu nhập người đồng vay (`thu_nhap_nguoi_dong_vay_vnd`), Giá trị tài sản đảm bảo (`gia_tri_tai_san_dam_bao_vnd`), Số tiền vay (`so_tien_vay_vnd`).
  - Chuẩn đánh giá tín dụng Việt Nam: Điểm tín dụng CIC (`diem_tin_dung_cic`), Phân nhóm nợ CIC (`nhom_no_cic`: Nhóm 1 - Nhóm 5), Số lần trễ hạn 2 năm, Tiền sử nợ xấu, Tỷ lệ DTI.
  - Nhãn phê duyệt: `phe_duyet_khoan_vay` (1: Phê duyệt, 0: Bị từ chối).
- **Lý do & Tái lập:** Mô phỏng sát thực tế quan hệ tín dụng các ngân hàng thương mại Việt Nam (Vietcombank, VPBank, Techcombank, MBBank...) với seed cố định (seed = 42).

---

### 2. Giả định về Đặc trưng và Thuộc tính Tài chính (Feature Assumptions)
- **Điểm tín dụng (Credit Score):** Thang điểm chuẩn CIC Việt Nam từ 400 đến 850 (theo Quyết định số 13/2010/QĐ-NHNN và chuẩn Trung tâm Thông tin Tín dụng Quốc gia CIC):
  - 400 - 579: Kém / Rủi ro cao (Hạng 9 - 10)
  - 580 - 669: Trung bình (Hạng 7 - 8)
  - 670 - 739: Khá (Hạng 5 - 6)
  - 740 - 799: Tốt (Hạng 3 - 4)
  - 800 - 850: Xuất sắc (Hạng 1 - 2)
- **Tỷ lệ Nợ trên Thu nhập (DTI - Debt-to-Income):**
  - DTI lý tưởng: Dưới 36%.
  - DTI cảnh báo: Từ 36% đến 50%.
  - DTI rủi ro cao: Trên 50%.
- **Tỷ lệ Vay trên Giá trị Tài sản đảm bảo (LTV - Loan-to-Value):**
  - LTV an toàn: Dưới 80%.
  - LTV rủi ro: Trên 80% (yêu cầu thêm bảo hiểm khoản vay hoặc xét duyệt nghiêm ngặt).
- **Lịch sử vi phạm (Delinquency / Derogatory):** Khách hàng có trên 2 lần trễ hạn thanh toán trong 2 năm gần nhất sẽ chịu tỷ lệ từ chối cao hơn đáng kể.

---

### 3. Giả định về Mục tiêu Tối ưu hóa Nghiệp vụ (Business Objective Assumption)
- **Đánh đổi chi phí sai sót tín dụng:**
  - **False Positive (FP - Duyệt người có rủi ro vỡ nợ cao):** Gây thiệt hại tài chính trực tiếp (mất vốn gốc + chi phí xử lý nợ xấu). Chi phí ước tính gấp 3-5 lần so với FN.
  - **False Negative (FN - Từ chối người vay tốt):** Thiệt hại cơ hội (mất doanh thu lãi vay tiềm năng).
- **Quyết định tối ưu:** Do đó, hệ thống ưu tiên tối ưu hóa **ROC-AUC** và **Precision/Recall cân bằng (F1-score trên nhóm rủi ro)**, cùng với việc tinh chỉnh ngưỡng quyết định (threshold tuning) sao cho giảm thiểu tối đa False Positive mà vẫn duy trì tỷ lệ phê duyệt hợp lý (khoảng 60-70%).

---

### 4. Giả định về Đạo đức và Công bằng (Fairness & Ethics Assumption)
- Các biến nhân khẩu học nhạy cảm như `gioi_tinh`, `tinh_trang_hon_nhan`, `tuoi` có tham gia làm đặc trưng đầu vào của mô hình, nhưng được giám sát chặt chẽ qua Kiểm toán Công bằng (DIR/EOD) định kỳ nhằm đảm bảo tuân thủ quy chuẩn tín dụng công bằng (Fair Lending Regulations). Xem chi tiết tại `reports/explainability.md` Mục 3.

---

### 5. Giả định về Quy tắc Loại trừ Cứng (Hard Policy Knockout Rules)
- **Đồng bộ giữa lớp sinh dữ liệu và Decision Engine:** Cả `src/data_generator.py` (dòng gán nhãn) lẫn `src/decision.py` (`HardRulesEngine.check_policy()`) đều áp dụng chung nguyên tắc:
  - **Nhóm nợ CIC 3 (Dưới tiêu chuẩn), Nhóm 4 (Nghi ngờ), Nhóm 5 (Mất vốn):** Tự động từ chối phê duyệt, không phụ thuộc xác suất mô hình ML.
  - **Điểm CIC < 450:** Tự động từ chối trong lớp sinh dữ liệu (`prob_approved = 0`).
  - **Tiền sử nợ xấu + Điểm CIC < 540:** Tự động từ chối trong Decision Engine.
- **Lý do thiết kế:** Đảm bảo lớp chính sách cứng (policy backstop) đồng bộ 100% với giả định nghiệp vụ đã đặt ra khi tạo nhãn dữ liệu huấn luyện, tránh tình trạng Decision Engine phụ thuộc hoàn toàn vào xác suất mô hình cho các trường hợp đã có quy tắc cứng rõ ràng.
