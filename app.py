import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import io
import qrcode

st.title("📦 Bullwhip Effect Decision Lab")

TARGET = 1.8
SERVICE_TARGET = 0.95

st.header(f"🎯 Challenge: Reduce Bullwhip below {TARGET} at ALL stages AND Maintain Service Level ≥ {int(SERVICE_TARGET*100)}%")

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
order_multiplier = st.sidebar.slider("Shortage Gaming", 1.0, 2.0, 1.3)
info_sharing = st.sidebar.checkbox("Information Sharing", value=False)

np.random.seed(42)

mean_demand = 100
std_demand = 20
customer_demand = np.random.normal(mean_demand, std_demand, T)

# ---- Promotion Shock ----
customer_demand[180:200] += 80

stages = 4
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand
inventory_position = np.ones((stages, T)) * mean_demand * (lead_time + 1)
stockouts = np.zeros((stages, T))

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
        inflated_order = order_multiplier * raw_order
        orders[i, t] = inflated_order

        inventory_position[i, t] = inventory_position[i, t-1] + orders[i, t] - demand

        if inventory_position[i, t] < 0:
            stockouts[i, t] = 1

# ---------------- Bullwhip ---------------- #

bullwhip = []
for i in range(stages):
    ratio = np.var(orders[i, 100:]) / np.var(customer_demand[100:])
    bullwhip.append(ratio)

stage_names = ["Retailer", "Wholesaler", "Distributor", "Manufacturer"]

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

st.subheader("🏆 Stability Score")
st.write(f"Score (Lower is Better): {avg_bullwhip + 2*(1 - avg_service):.2f}")

success = all(r < TARGET for r in bullwhip) and all(s >= SERVICE_TARGET for s in service_levels)

if success:
    st.success("✅ Challenge Completed! Balanced and Stable Supply Chain.")
else:
    st.warning("⚠ Not Yet Stable. Adjust Decisions.")

# ---------------- 2x2 Plots ---------------- #

colors = ["blue", "orange", "green", "red"]
fig, axs = plt.subplots(2, 2, figsize=(12,8))
axs = axs.flatten()

for i in range(stages):
    axs[i].plot(customer_demand, label="Customer Demand", color="darkgray", linewidth=2)
    axs[i].plot(orders[i], label=f"{stage_names[i]} Orders", color=colors[i])
    axs[i].set_title(f"{stage_names[i]} vs Customer Demand")
    axs[i].legend()

plt.tight_layout()
st.pyplot(fig)

# ---------------- Bar Plot ---------------- #

fig2, ax2 = plt.subplots()
ax2.bar(stage_names, bullwhip, color=colors)
ax2.axhline(1, linestyle="--", color="black")
ax2.set_title("Bullwhip Amplification Across Supply Chain")
ax2.set_ylabel("Variance Ratio")
st.pyplot(fig2)