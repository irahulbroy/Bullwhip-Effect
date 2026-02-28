import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import io
import qrcode

st.title("📦 Bullwhip Effect Decision Lab")

TARGET = 1.5
SERVICE_TARGET = 0.95

st.header(f"🎯 Challenge: Reduce Bullwhip ≤ {TARGET} at ALL stages AND Maintain Service Level ≥ {int(SERVICE_TARGET*100)}%")

st.markdown("""
Supply Chain:  
Customer → Retailer → Wholesaler → Distributor → Manufacturer  

Balance stability (low bullwhip) and responsiveness (high service level).
""")

# ---------------- Sidebar ---------------- #
st.sidebar.header("Decision Variables")

T = 400
lead_time = st.sidebar.slider("Lead Time", 1, 8, 4)
alpha = st.sidebar.slider("Forecast Responsiveness (α)", 0.01, 1.0, 0.6)
order_multiplier = st.sidebar.slider("Order Cushioning (Shortage Gaming)", 1.0, 2.0, 1.3)
info_sharing = st.sidebar.checkbox("Information Sharing", value=False)

np.random.seed()  # Randomize each run

mean_demand = 100
std_demand = 20
customer_demand = np.random.normal(mean_demand, std_demand, T)

# ---- Dynamic Promotion Shock ----
shock_start = np.random.randint(100, 300)
shock_length = np.random.randint(5, 20)
shock_magnitude = np.random.randint(50, 100)
customer_demand[shock_start:shock_start+shock_length] += shock_magnitude

st.subheader(f"💥 Promotion Spike: t={shock_start}-{shock_start+shock_length-1}, +{shock_magnitude}")

stages = 4
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand
inventory_position = np.ones((stages, T)) * mean_demand * (lead_time + 1)
stockouts = np.zeros((stages, T))

stage_names = ["Retailer", "Wholesaler", "Distributor", "Manufacturer"]

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
        base_stock = forecast[i, t] * (lead_time + 1)

        raw_order = base_stock - inventory_position[i, t-1]
        orders[i, t] = order_multiplier * raw_order
        inventory_position[i, t] = inventory_position[i, t-1] + orders[i, t] - demand

        if inventory_position[i, t] < 0:
            stockouts[i, t] = 1

# ---------------- Bullwhip ---------------- #
bullwhip = [np.var(orders[i, 100:]) / np.var(customer_demand[100:]) for i in range(stages)]

st.subheader("📊 Bullwhip Ratios")
for i in range(stages):
    st.write(f"{stage_names[i]}: {bullwhip[i]:.2f}")

# ---------------- Service Level ---------------- #
service_levels = 1 - stockouts.mean(axis=1)
st.subheader("📦 Service Levels")
for i in range(stages):
    st.write(f"{stage_names[i]}: {service_levels[i]*100:.1f}%")

# ---------------- Scoreboard ---------------- #
avg_bullwhip = np.mean(bullwhip)
avg_service = np.mean(service_levels)
stability_score = avg_bullwhip + 2*(1 - avg_service)
st.subheader("🏆 Stability Score")
st.write(f"Score (Lower is Better): {stability_score:.2f}")

success = all(r <= TARGET for r in bullwhip) and all(s >= SERVICE_TARGET for s in service_levels)
if success:
    st.success("✅ Challenge Completed!")
else:
    st.warning("⚠ Keep experimenting to balance stability & service.")

# ---------------- Customer Demand Plot ---------------- #
fig_cust, ax = plt.subplots(figsize=(14,4))
ax.plot(customer_demand, color="black", label="Customer Demand", linewidth=2)
ax.set_title("Customer Demand (with Dynamic Shock)")
ax.legend()
st.pyplot(fig_cust)

# ---------------- 2x2 Stage Plots ---------------- #
colors = ["blue", "orange", "green", "red"]
fig, axs = plt.subplots(2, 2, figsize=(14,10))
axs = axs.flatten()
for i in range(stages):
    axs[i].plot(customer_demand, label="Customer Demand", color="black", linewidth=1.5)
    axs[i].plot(orders[i], label=f"{stage_names[i]} Orders", color=colors[i], linewidth=2)
    axs[i].set_title(f"{stage_names[i]} vs Customer Demand")
    axs[i].legend()
plt.tight_layout()
st.pyplot(fig)