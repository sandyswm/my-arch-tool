import streamlit as st
import pandas as pd
from io import BytesIO

# 页面配置
st.set_page_config(page_title="建筑师强排助手 v1.0", layout="wide")

# --- 1. 样式与标题 ---
st.title("🏗️ 建筑策划：强排指标与货值测算工具")
st.markdown("---")

# --- 2. 会话状态初始化 (用于滑动条联动) ---
if 'res_ratio' not in st.session_state:
    st.session_state.res_ratio = 80
if 'com_ratio' not in st.session_state:
    st.session_state.com_ratio = 20

def update_res():
    st.session_state.com_ratio = 100 - st.session_state.res_ratio

def update_com():
    st.session_state.res_ratio = 100 - st.session_state.com_ratio

# --- 3. 侧边栏：地块基础参数 ---
st.sidebar.header("📍 地块基础参数")
site_area = st.sidebar.number_input("地块面积 (㎡)", value=10000.0, step=100.0)
target_far = st.sidebar.number_input("规划容积率", value=2.5, step=0.1)
max_density_pct = st.sidebar.number_input("建筑密度上限 (%)", value=30.0, step=1.0)
land_cost_cr = st.sidebar.number_input("土地获取成本 (亿元)", value=5.0, step=0.1)

# 计算计容上限
max_allowed_area = site_area * target_far
max_base_area = site_area * (max_density_pct / 100)

# --- 4. 主界面：功能配比与面积计算 ---
st.header("1. 功能配比与计容面积")
col1, col2 = st.columns([2, 1])

with col1:
    st.write("**调整业态比例 (总计100%)**")
    c_res, c_com = st.columns(2)
    with c_res:
        res_ratio = st.slider("住宅比例 (%)", 0, 100, key="res_ratio", on_change=update_res)
    with c_com:
        com_ratio = st.slider("商业比例 (%)", 0, 100, key="com_ratio", on_change=update_com)
    
    # 面积分配计算
    res_area = max_allowed_area * (res_ratio / 100)
    com_area = max_allowed_area * (com_ratio / 100)
    total_calc_area = res_area + com_area

    # 细化指标
    avg_unit_size = st.number_input("住宅平均户型面积 (㎡)", value=110)
    parking_rate = st.number_input("车位配比 (个/100㎡计容)", value=1.0)
    total_units = int(res_area / avg_unit_size)
    total_parking = int(total_calc_area * (parking_rate / 100))

with col2:
    st.metric("总计容建筑面积", f"{total_calc_area:,.2f} ㎡")
    if total_calc_area > max_allowed_area:
        st.error(f"⚠️ 超容! 超出 {total_calc_area - max_allowed_area:.2f} ㎡")
    else:
        st.success("✅ 容积率达标")
    st.metric("估算住宅总户数", f"{total_units} 户")
    st.metric("建议配建停车位", f"{total_parking} 个")

# --- 5. 不计容空间与成本核算 ---
st.markdown("---")
st.header("2. 不计容空间与建设成本")
col3, col4 = st.columns(2)

with col3:
    st.write("**不计容参数**")
    void_layer_ratio = st.slider("住宅架空层比例 (%)", 0, 10, 3) / 100
    basement_per_car = st.number_input("地下单车位指标 (㎡/个)", value=35.0)
    
    void_area = res_area * void_layer_ratio
    basement_area = total_parking * basement_per_car
    total_non_calc_area = void_area + basement_area
    total_build_area = total_calc_area + total_non_calc_area

with col4:
    st.write("**造价标准 (元/㎡)**")
    cost_above = st.number_input("地上单方造价", value=4500)
    cost_below = st.number_input("地下单方造价", value=6000)
    
    total_cost_cr = (total_calc_area * cost_above + basement_area * cost_below) / 100000000

st.info(f"**总建筑面积测算：{total_build_area:,.2f} ㎡** (含地下不计容 {basement_area:,.0f} ㎡)")

# --- 6. 货值与利润评估 ---
st.markdown("---")
st.header("3. 经济性分析 (货值测算)")
col5, col6, col7 = st.columns(3)

with col5:
    p_res = st.number_input("住宅均价 (元/㎡)", value=25000)
with col6:
    p_com = st.number_input("商业均价 (元/㎡)", value=45000)
with col7:
    p_park = st.number_input("车位单价 (万元/个)", value=15.0) * 10000

val_res = res_area * p_res / 100000000
val_com = com_area * p_com / 100000000
val_park = total_parking * p_park / 100000000
total_value_cr = val_res + val_com + val_park
net_profit_cr = total_value_cr - total_cost_cr - land_cost_cr

m_a, m_b, m_c = st.columns(3)
m_a.metric("总销售货值", f"{total_value_cr:.2f} 亿元")
m_b.metric("总建设成本", f"{total_cost_cr:.2f} 亿元")
m_c.metric("预计毛利润", f"{net_profit_cr:.2f} 亿元", delta=f"利润率 {(net_profit_cr/total_value_cr)*100:.1f}%" if total_value_cr >0 else "0%")

# --- 7. 数据导出模块 ---
st.markdown("---")
st.subheader("📊 导出策划报告")

report_df = pd.DataFrame({
    "指标分类": ["地块信息"] * 3 + ["面积指标"] * 5 + ["经济指标"] * 4,
    "项目名称": [
        "地块面积", "规划容积率", "土地成本",
        "计容总面积", "住宅面积", "商业面积", "地下室面积", "总建筑面积",
        "总销售货值", "总建设成本", "预计毛利润", "静态利润率"
    ],
    "数值": [
        f"{site_area:,.0f}", f"{target_far}", f"{land_cost_cr}亿",
        f"{total_calc_area:,.2f}", f"{res_area:,.2f}", f"{com_area:,.2f}", f"{basement_area:,.2f}", f"{total_build_area:,.2f}",
        f"{total_value_cr:.2f}亿", f"{total_cost_cr:.2f}亿", f"{net_profit_cr:.2f}亿", f"{(net_profit_cr/total_value_cr)*100:.1f}%"
    ],
    "单位": ["㎡", "-", "亿元", "㎡", "㎡", "㎡", "㎡", "㎡", "亿元", "亿元", "亿元", "%"]
})

st.table(report_df)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='强排测算')
    return output.getvalue()

st.download_button(
    label="📥 下载 Excel 完整报表",
    data=to_excel(report_df),
    file_name="建筑强排测算报告.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
