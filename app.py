import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="电商经营异常诊断", page_icon="🛒", layout="wide")
st.title("🛒 电商经营异常诊断与增长优化系统")
st.caption("作品集演示｜全部为合成模拟数据，不代表真实企业")
@st.cache_data
def load():
    return (pd.read_csv("daily_ecommerce_metrics.csv", parse_dates=["date"]),
            pd.read_csv("product_performance.csv"))
df, products = load()
with st.sidebar:
    st.header("分析设置")
    dates=st.date_input("分析日期范围",(df.date.min().date(),df.date.max().date()))
    threshold_note="先看整体趋势，再拆解流量、转化率、客单价、广告效率和商品利润。"
    st.write(threshold_note)
if isinstance(dates,tuple) and len(dates)==2:
    data=df[(df.date>=pd.Timestamp(dates[0]))&(df.date<=pd.Timestamp(dates[1]))].copy()
else: data=df.copy()
if data.empty:
    st.warning("该日期范围无数据。"); st.stop()
st.subheader("一、经营总览")
a,b,c,d,e=st.columns(5)
a.metric("销售额",f"¥{data.revenue.sum():,.0f}")
b.metric("访问量",f"{data.sessions.sum():,}")
c.metric("订单量",f"{data.orders.sum():,}")
d.metric("支付转化率",f"{data.orders.sum()/data.sessions.sum():.2%}")
e.metric("广告 ROAS",f"{data.revenue.sum()/data.ad_spend.sum():.2f}x")
l,r=st.columns(2)
with l:
    st.markdown("**每日销售额趋势**"); st.line_chart(data.set_index("date")[["revenue"]])
with r:
    st.markdown("**流量与订单趋势**"); st.line_chart(data.set_index("date")[["sessions","orders"]])
st.subheader("二、经营异常诊断")
mid=max(1,len(data)//2); prev,curr=data.iloc[:mid],data.iloc[mid:]
metrics=[("销售额",prev.revenue.mean(),curr.revenue.mean()),("访问量",prev.sessions.mean(),curr.sessions.mean()),
("转化率",prev.conversion_rate.mean(),curr.conversion_rate.mean()),("客单价",prev.aov.mean(),curr.aov.mean()),
("广告花费",prev.ad_spend.mean(),curr.ad_spend.mean()),("ROAS",prev.roas.mean(),curr.roas.mean()),
("退款率",prev.refund_rate.mean(),curr.refund_rate.mean()),("估算毛利",prev.estimated_gross_profit.mean(),curr.estimated_gross_profit.mean())]
m=pd.DataFrame(metrics,columns=["指标","前半周期日均","后半周期日均"])
m["变化率"]=[(b-a)/abs(a) if a else np.nan for _,a,b in metrics]
st.dataframe(m.style.format({"前半周期日均":"{:,.2f}","后半周期日均":"{:,.2f}","变化率":"{:+.1%}"}),use_container_width=True)
st.info("销售额可拆解为流量 × 转化率 × 客单价。先定位变化，再按渠道、活动、设备和用户类型下钻；趋势只能提供线索，不能单独证明因果。")
st.subheader("三、商品运营：高销售额不等于高利润")
cat=products.groupby("category",as_index=False).agg(revenue=("revenue","sum"),estimated_profit=("estimated_profit","sum"),
units_sold=("units_sold","sum"),avg_return_rate=("return_rate","mean"),avg_discount=("discount_rate","mean"))
l,r=st.columns(2)
with l:
    st.markdown("**品类销售额**"); st.bar_chart(cat.set_index("category")[["revenue"]])
with r:
    st.markdown("**品类估算利润**"); st.bar_chart(cat.set_index("category")[["estimated_profit"]])
st.dataframe(cat.sort_values("estimated_profit",ascending=False).style.format({"revenue":"¥{:,.0f}","estimated_profit":"¥{:,.0f}","avg_return_rate":"{:.1%}","avg_discount":"{:.1%}"}),use_container_width=True)
products["operation_tag"]=np.select([
(products.estimated_profit>products.estimated_profit.quantile(.75))&(products.return_rate<products.return_rate.median()),
(products.revenue>products.revenue.quantile(.75))&(products.estimated_profit<products.estimated_profit.median()),
products.return_rate>products.return_rate.quantile(.75)],
["利润优先推广","高销售低利润：检查折扣/成本","高退货：排查质量/描述"],default="常规观察")
st.markdown("**商品运营清单**")
st.dataframe(products.sort_values("estimated_profit",ascending=False),use_container_width=True,height=380)
st.download_button("下载商品运营清单 CSV",products.to_csv(index=False).encode("utf-8-sig"),"product_operation_list.csv","text/csv")
st.subheader("四、建议与效果验证")
st.markdown("""
1. **流量异常：** 按自然流量、付费渠道、活动和设备拆分，检查流量结构变化。
2. **转化异常：** 分析详情页访问→加购→提交订单→支付成功漏斗，定位流失环节。
3. **广告效率：** 同时看 ROAS 与毛利，不只追求销售额；对低效计划小预算测试后再调整。
4. **商品策略：** 高利润低退货商品优先曝光；高销售低利润商品复核折扣和成本；高退货商品排查质量及详情描述。
5. **验证结果：** 设置实验组/对照组，追踪转化率、增量毛利、退款率和新客占比。
""")
st.caption("注意：ROAS 分子在此用总销售额作演示，正式项目应使用平台归因销售额。估算毛利为简化口径，实际需纳入商品成本、平台佣金、履约成本及退款损失。")
