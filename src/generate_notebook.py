import json
import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Giai đoạn 1: Khám phá Dữ liệu Tín dụng Khách hàng Việt Nam (EDA)\n",
                "## Hệ thống Dự đoán Khả năng Phê duyệt Khoản vay\n",
                "\n",
                "Notebook này thực hiện các bước chuẩn chỉnh:\n",
                "1. Nạp và kiểm tra cấu trúc dữ liệu hồ sơ vay vốn Việt Nam (`data/raw/loan_data.csv`).\n",
                "2. Thống kê mô tả (Descriptive Statistics) các trường thông tin tài chính VNĐ.\n",
                "3. Phân tích giá trị thiếu (Missing Values) & ngoại lai (Outliers).\n",
                "4. Phân tích phân bố nhãn mục tiêu `phe_duyet_khoan_vay`.\n",
                "5. Đánh giá tác động của Điểm tín dụng CIC và Nhóm nợ CIC."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 1,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "\n",
                "sns.set_theme(style='whitegrid')\n",
                "df = pd.read_csv('../data/raw/loan_data.csv', encoding='utf-8-sig')\n",
                "print(f'Kích thước dữ liệu: {df.shape}')\n",
                "df.head()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 2,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Kiểm tra thông tin kiểu dữ liệu và giá trị thiếu\n",
                "df.info()\n",
                "print('\\nSố giá trị thiếu theo từng cột:\\n', df.isnull().sum()[df.isnull().sum() > 0])"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 3,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Thống kê mô tả các biến số tài chính\n",
                "df.describe().T"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 4,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Tỷ lệ phê duyệt khoản vay\n",
                "approval_counts = df['phe_duyet_khoan_vay'].value_counts(normalize=True) * 100\n",
                "print('Tỷ lệ phê duyệt (%):\\n', approval_counts)\n",
                "\n",
                "plt.figure(figsize=(6, 4))\n",
                "sns.countplot(data=df, x='phe_duyet_khoan_vay', palette=['#e74c3c', '#2ecc71'])\n",
                "plt.title('Tỷ lệ Phê duyệt Khoản vay (0: Từ chối, 1: Phê duyệt)')\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": 5,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Phân tích Điểm tín dụng CIC và Tỷ lệ DTI theo trạng thái duyệt\n",
                "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
                "sns.boxplot(data=df, x='phe_duyet_khoan_vay', y='diem_tin_dung_cic', ax=axes[0], palette=['#e74c3c', '#2ecc71'])\n",
                "axes[0].set_title('Điểm CIC vs Phê duyệt')\n",
                "\n",
                "sns.boxplot(data=df, x='phe_duyet_khoan_vay', y='ty_le_dti', ax=axes[1], palette=['#e74c3c', '#2ecc71'])\n",
                "axes[1].set_title('Tỷ lệ DTI (%) vs Phê duyệt')\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        }
    ],
    "metadata": {
        "language_info": {
            "name": "python"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

os.makedirs("notebooks", exist_ok=True)
with open("notebooks/01_eda.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2, ensure_ascii=False)
print("Đã cập nhật notebooks/01_eda.ipynb tiếng Việt thành công.")
