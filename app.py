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

**Formulas:**  
- Bullwhip Ratio = Var(Stage Orders) / Var(Customer Demand)  
- Stability Score = Avg Bullwhip + 2 × (1 − Avg Service Level)
""")

# ---------------- Sidebar ---------------- #
st.sidebar.header("Decision Variables")

T = 400
lead_time = st.sidebar.slider("Lead Time", 1, 8, 4)  # realistic L
alpha = st.sidebar.slider("Forecast Responsiveness (α)", 0.05, 0.9, 0.4)  # min>0
order_multiplier = st.sidebar.slider("Order Cushioning (Shortage Gaming)", 1.0, 2.0, 1.3)
info_sharing = st.sidebar.checkbox("Information Sharing", value=False)

np.random.seed()  # dynamic shocks each run

mean_demand = 100
std_demand = np.random.randint(15, 30)  # random baseline variance each run
customer_demand = np.random.normal(mean_demand, std_demand, T)

# ---- Random Dynamic Shocks ----
num_shocks = np.random.randint(1, 4)  # 1–3 spikes
for _ in range(num_shocks):
    shock_start = np.random.randint(50, T-20)
    shock_length = np.random.randint(5, 20)
    shock_magnitude = np.random.randint(50, 100)
    customer_demand[shock_start:shock_start+shock_length] += shock_magnitude

stages = 4
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand
inventory_position = np.ones((stages, T)) * mean_demand * (lead_time + 1)
stockouts = np.zeros((stages, T))

stage_names = ["Retailer", "Wholesaler", "Distributor", "Manufacturer"]

# ---- Simulation ----
for t in range(1, T):
    for i in range(stages):
        if i == 0:
            demand = customer_demand[t]
        else:
            demand = orders[i-1, t-1]

        if info_sharing:
            demand_for_forecast = customer_demand[t]
        else:
            demand_for_forecast = demand

        forecast[i, t] = alpha * demand_for_forecast + (1 - alpha) * forecast[i, t-1]
        
        # Add small safety stock random noise to prevent trivial low L solution
        safety_stock = np.random.randint(5, 15)
        base_stock = forecast[i, t] * (lead_time + 1) + safety_stock

        raw_order = base_stock - inventory_position[i, t-1]
        orders[i, t] = order_multiplier * raw_order
        inventory_position[i, t] = inventory_position[i, t-1] + orders[i, t] - demand

        if inventory_position[i, t] < 0:
            stockouts[i, t] = 1

# ---- Bullwhip Ratios ----
bullwhip = [np.var(orders[i, 100:]) / np.var(customer_demand[100:]) for i in range(stages)]

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

# ---- Stability Score ----
avg_bullwhip = np.mean(bullwhip)
avg_service = np.mean(service_levels)
stability_score = avg_bullwhip + 2*(1 - avg_service)
st.subheader("🏆 Stability Score")
st.write(f"Score (Lower is Better): {stability_score:.2f}")

# ---- Challenge Status ----
success = all(r <= TARGET for r in bullwhip) and all(s >= SERVICE_TARGET for s in service_levels)
if success:
    st.success("✅ Challenge Completed!")
else:
    st.warning("⚠ Not Yet Stable")

# ---- Customer Demand Plot ----
fig_cust, ax = plt.subplots(figsize=(14,4))
ax.plot(customer_demand, color="black", label="Customer Demand", linewidth=2)
ax.set_title("Customer Demand (with Random Shocks)")
ax.legend()
st.pyplot(fig_cust)

# ---- 2x2 Stage Plots ----
colors = ["blue", "orange", "green", "red"]
fig, axs = plt.subplots(2, 2, figsize=(16,12))
axs = axs.flatten()
for i in range(stages):
    axs[i].plot(orders[i], label=f"{stage_names[i]} Orders", color=colors[i], linewidth=2)
    axs[i].set_title(f"{stage_names[i]} Orders Over Time")
    axs[i].legend()
plt.tight_layout()
st.pyplot(fig)