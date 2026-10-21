# -*- coding: utf-8 -*-
"""生成两个演示用测试数据集（纯标准库实现，无需额外依赖）。

运行：python data/generate_samples.py
产物：data/sample_sales.csv（电商销售数据）、data/sample_iris.csv（鸢尾花数据）
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # 固定随机种子，保证每次生成结果一致、可复现
OUT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# 1. 电商销售数据 sample_sales.csv
# ---------------------------------------------------------------------------
REGIONS = ["华东", "华南", "华北", "西南", "东北"]
CATEGORIES = {
    "电子产品": ["智能手机", "笔记本电脑", "蓝牙耳机", "智能手表"],
    "服装": ["T恤", "牛仔裤", "连衣裙", "运动鞋"],
    "食品": ["坚果礼盒", "咖啡豆", "巧克力", "茶叶"],
    "家居": ["床品四件套", "台灯", "收纳箱", "香薰蜡烛"],
    "美妆": ["口红", "面霜", "香水", "面膜"],
}
SEGMENTS = ["个人", "企业", "VIP"]
PRICE_RANGE = {
    "电子产品": (299, 9999),
    "服装": (39, 899),
    "食品": (19, 499),
    "家居": (29, 1599),
    "美妆": (59, 1299),
}
MARGIN = {"电子产品": 0.10, "服装": 0.35, "食品": 0.20, "家居": 0.30, "美妆": 0.45}

N = 500
START = date(2023, 1, 1)
sales_rows = []
for i in range(1, N + 1):
    cat = random.choice(list(CATEGORIES))
    lo, hi = PRICE_RANGE[cat]
    unit_price = round(random.uniform(lo, hi), 2)
    quantity = random.randint(1, 10)
    sales = round(unit_price * quantity, 2)
    profit = round(sales * MARGIN[cat] * random.gauss(1.0, 0.15), 2)
    sales_rows.append([
        f"ORD-{i:05d}",
        (START + timedelta(days=random.randint(0, 729))).isoformat(),
        random.choice(REGIONS),
        cat,
        random.choice(CATEGORIES[cat]),
        quantity,
        unit_price,
        sales,
        profit,
        random.choices(SEGMENTS, weights=[0.6, 0.25, 0.15])[0],
    ])

# 人为制造少量缺失值，用于演示「数据清洗预检」
for col_idx in (8, 2):  # profit / region 两列各挖 5 个空值
    for _ in range(5):
        sales_rows[random.randrange(N)][col_idx] = ""

with open(OUT / "sample_sales.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["order_id", "order_date", "region", "category", "product",
                "quantity", "unit_price", "sales", "profit", "customer_segment"])
    w.writerows(sales_rows)

# ---------------------------------------------------------------------------
# 2. 鸢尾花数据 sample_iris.csv（三个高斯簇模拟经典 iris 结构）
# ---------------------------------------------------------------------------
CLUSTERS = [
    ("setosa", (5.0, 3.4, 1.5, 0.2), (0.6, 0.6, 0.4, 0.2)),
    ("versicolor", (5.9, 2.7, 4.2, 1.3), (0.7, 0.55, 0.65, 0.3)),
    ("virginica", (6.6, 3.0, 5.5, 2.0), (0.8, 0.6, 0.75, 0.4)),
]
iris_rows = []
for species, center, sigma in CLUSTERS:
    for _ in range(50):
        iris_rows.append([
            round(random.gauss(center[0], sigma[0]), 1),
            round(random.gauss(center[1], sigma[1]), 1),
            round(random.gauss(center[2], sigma[2]), 1),
            round(random.gauss(center[3], sigma[3]), 1),
            species,
        ])
random.shuffle(iris_rows)

with open(OUT / "sample_iris.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["sepal_length", "sepal_width", "petal_length", "petal_width", "species"])
    w.writerows(iris_rows)

print(f"生成完成：sample_sales.csv（{len(sales_rows)} 行）、sample_iris.csv（{len(iris_rows)} 行）")
