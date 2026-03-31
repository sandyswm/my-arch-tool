import streamlit as st
import pandas as pd
from io import BytesIO

# 1. 基础配置（必须在最前）
st.set_page_config(page_title="建筑师强排助手", layout="wide", initial_sidebar_state="collapsed")

# --- 核心：更稳定的联动逻辑 ---
if 'res_ratio' not in st.session_state:
    st.session_state.res_ratio = 80

# 住宅比例改变时，自动算商业
def on_res_change():
    st.session_state.com_ratio = 100 - st.session_state.res_ratio

# 商业比例改变时，自动算住宅
def on_com_change():
    st.session_state.res_ratio = 100 - st.session_state.com_ratio

if 'com_ratio' not in st.session_state:
    st.session_state.com_ratio = 20

# --- 界面开始 ---
st.title("🏗️ 建筑强排测算 (手机适配版)")

# 侧边栏：基础参数
with st.sidebar:
    st.header("📍 地块参数")
    site_area = st.number_input("地块面积 (㎡)", value=10000.0)
    target_far = st.number_input("规划容积率", value=2.5)
    max_density = st.number_input("密度上限 (%)", value=30.0) / 100
    land_cost = st.number_input("土地成本 (亿元)", value=5.0)

# 计算上限
max_allowed_area = site_area * target_far

# 主界面
st.subheader("1. 业态配比")
col_a, col_b = st.columns(2)
with col_a:
    res_pct = st.slider("住宅比例 %", 0, 100, key="res_ratio", on_change=on_res_change)
with col_b:
    com_pct = st.slider("商业比例 %", 0, 100, key="com_ratio", on_change=on_com_change)

# 面积计算
res_area = max_allowed_area * (res_pct / 100)
com_area = max_allowed_area * (com_pct / 100)
total_calc_area = res_area + com_area

# 户数与车位
st.markdown("---")
col_c, col_d = st.columns(2)
with col_c:
    unit_size = st.number_input("住宅平均户型 (㎡)", value=110)
    park_rate = st.number_input("车位配比 (个/100㎡)", value=1.0)
with col_d:
    total_units = int(res_area / unit_size) if unit_size > 0 else 0
    total_parking = int(total_calc_area * (park_rate / 100))
    st.metric("总户数", f"{total_units} 户")
    st.metric("总车位", f"{total_parking} 个")

# 不计容与成本
st.subheader("2. 成本与造价")
c1, c2 = st.columns(2)
with c1:
    base_per_car = st.number_input("地下单车位指标 (㎡)", value=35.0)
    cost_up = st.number_input("地上造价 (元/㎡)", value=4500)
with c2:
    cost_down = st.number_input("地下造价 (元/㎡)", value=6000)

base_area = total_parking * base_per_car
total_build_area = total_calc_area + base_area
total_cost = (total_calc_area * cost_up + base_area * cost_down) / 100000000

# 货值分析
st.subheader("3. 货值分析")
p1, p2 = st.columns(2)
with p1:
    pr_res = st.number_input("住宅均价 (元/㎡)", value=25000)
with p2:
    pr_com = st.number_input("商业均价 (元/㎡)", value=45000)

total_val = (res_area * pr_res + com_area * pr_com) / 100000000
profit = total_val - total_cost - land_cost

st.divider()
st.metric("项目总货值", f"{total_val:.2f} 亿元")
st.metric("预计毛利润", f"{profit:.2f} 亿元", delta=f"利润率 {profit/total_val*100:.1f}%" if total_val >0 else "0%")

# 导出
st.subheader("4. 数据导出")
report_df = pd.DataFrame({
    "项目": ["计容面积", "住宅面积", "商业面积", "地下面积", "总货值", "总成本", "利润"],
    "数值": [f"{total_calc_area:.1f}", f"{res_area:.1f}", f"{com_area:.1f}", f"{base_area:.1f}", f"{total_val:.2f}亿", f"{total_cost:.2f}亿", f"{profit:.2f}亿"]
})
st.table(report_df)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button("📥 下载 Excel 报告", data=to_excel(report_df), file_name="策划报告.xlsx")
