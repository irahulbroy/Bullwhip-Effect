import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import io
import qrcode

st.title("📦 Bullwhip Effect Decision Lab")

TARGET = 1.5
SERVICE_TARGET = 0.95

st.header(f"🎯 Challenge: Reduce Bullwhip ≤ {TARGET} AND Maintain Service Level ≥ {int(SERVICE_TARGET*100)}%")

st.markdown("""
Supply Chain:  
Customer → Retailer → Wholesaler → Distributor → Manufacturer  

Balance stability (low bullwhip) and responsiveness (high service level).
""")

# ---------------- Sidebar ---------------- #
st.sidebar.header("Decision Variables")
T = 400
lead_time = st.sidebar.slider("Lead Time (L)", 1, 8, 4)
alpha = st.sidebar.slider("Forecast Responsiveness (α)", 0.05, 0.9, 0.4)
order_multiplier = st.sidebar.slider("Order Cushioning (Shortage Gaming)", 1.0, 2.0, 1.3)
safety_stock_multiplier = st.sidebar.slider("Safety Stock Multiplier", 0.5, 3.0, 1.0, 0.1)
info_sharing = st.sidebar.checkbox("Information Sharing", value=False)

np.random.seed()  # new run each time

# ---- Customer demand ----
mean_demand = 100
std_demand = np.random.randint(20, 50)
customer_demand = np.random.normal(mean_demand, std_demand, T)
original_customer_demand = customer_demand.copy()  # fixed copy for plotting

# ---- Hidden multiplicative spikes ----
for t in range(T):
    if np.random.rand() < 0.02:
        customer_demand[t] *= np.random.uniform(1.3, 1.6)

stages = 4
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand
inventory_position = np.ones((stages, T)) * mean_demand * (lead_time + 1)
stockouts = np.zeros((stages, T))
stage_names = ["Retailer", "Wholesaler", "Distributor", "Manufacturer"]

# ---- Simulation ----
for t in range(1, T):
    for i in range(stages):
        # Determine demand for this stage
        if i == 0:
            demand = customer_demand[t]
        else:
            demand = orders[i-1, t-1]

        # Forecast
        if info_sharing:
            demand_for_forecast = customer_demand[t]
        else:
            demand_for_forecast = demand

        forecast[i, t] = alpha * demand_for_forecast + (1 - alpha) * forecast[i, t-1]

        # Base stock with safety stock multiplier
        safety_stock = np.random.randint(5,15) * safety_stock_multiplier
        base_stock = forecast[i, t] * (lead_time + 1) + safety_stock

        raw_order = max(order_multiplier * (base_stock - inventory_position[i, t-1]), 0)
        orders[i, t] = raw_order
        inventory_position[i, t] = inventory_position[i, t-1] + orders[i, t] - demand

        if inventory_position[i, t] < 0:
            stockouts[i, t] = 1

# ---- Bullwhip Ratios ----
bullwhip = [np.var(orders[i, 100:]) / np.var(original_customer_demand[100:]) for i in range(stages)]

st.subheader("📊 Bullwhip Ratios")
for i in range(stages):
    if bullwhip[i] > TARGET:
        st.markdown(f"<span style='color:red'>{stage_names[i]}: {bullwhip[i]:.2f} (Exceeds Target)</span>", unsafe_allow_html=True)
    else:
        st.write(f"{stage_names[i]}: {bullwhip[i]:.2f}")

# ---- Service Levels ----
service_levels = 1 - stockouts.mean(axis=1)
st.subheader("📦 Service Levels")
for i in range(stages):
    st.write(f"{stage_names[i]}: {service_levels[i]*100:.1f}%")

# ---- Challenge Status ----
success = all(r <= TARGET for r in bullwhip) and all(s >= SERVICE_TARGET for s in service_levels)
if success:
    st.success("✅ Challenge Completed!")
else:
    st.warning("⚠ Not Yet Stable — Adjust parameters to find the sweet spot!")

# ---- Customer Demand Plot ----
fig_cust, ax = plt.subplots(figsize=(16,5))
ax.plot(original_customer_demand, color="black", label="Customer Demand", linewidth=3)
ax.set_title("Customer Demand", fontsize=20)
ax.set_xlabel("Time Period", fontsize=16)
ax.set_ylabel("Units", fontsize=16)
ax.tick_params(axis='both', labelsize=14)
ax.legend(fontsize=14)
st.pyplot(fig_cust)

# ---- 2x2 Stage Plots ----
colors = ["blue", "orange", "green", "red"]
fig, axs = plt.subplots(2, 2, figsize=(18,14))
axs = axs.flatten()
for i in range(stages):
    axs[i].plot(orders[i], label=f"{stage_names[i]} Orders", color=colors[i], linewidth=3)
    axs[i].set_title(f"{stage_names[i]} Orders Over Time", fontsize=18)
    axs[i].set_xlabel("Time Period", fontsize=14)
    axs[i].set_ylabel("Units Ordered", fontsize=14)
    axs[i].tick_params(axis='both', labelsize=14)
    axs[i].legend(fontsize=14)
plt.tight_layout()
st.pyplot(fig)