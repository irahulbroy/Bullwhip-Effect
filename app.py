import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("📦 Bullwhip Effect – Interactive Simulator")

st.sidebar.header("Simulation Parameters")

T = st.sidebar.slider("Time Periods", 50, 300, 150)
mean_demand = st.sidebar.slider("Mean Demand", 50, 200, 100)
std_demand = st.sidebar.slider("Demand Std Dev", 1, 50, 20)
lead_time = st.sidebar.slider("Lead Time", 1, 8, 3)
alpha = st.sidebar.slider("Forecast Smoothing (α)", 0.01, 1.0, 0.3)
safety_factor = st.sidebar.slider("Safety Stock Multiplier", 0.0, 3.0, 1.0)
info_sharing = st.sidebar.checkbox("Information Sharing (All use customer demand)")

np.random.seed(42)

# Generate customer demand
customer_demand = np.random.normal(mean_demand, std_demand, T)

stages = 4
inventory = np.zeros((stages, T))
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand

# Initial inventory
inventory[:, 0] = mean_demand * lead_time

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
        
        # Update forecast
        forecast[i, t] = alpha * demand_for_forecast + (1 - alpha) * forecast[i, t-1]
        
        target_inventory = forecast[i, t] * lead_time + safety_factor * std_demand
        
        # Inventory update
        inventory[i, t] = inventory[i, t-1] - demand
        
        # Order-up-to policy
        orders[i, t] = max(target_inventory - inventory[i, t], 0)
        
        # Receive shipment after lead time
        if t >= lead_time:
            inventory[i, t] += orders[i, t-lead_time]

# Compute bullwhip ratios
bullwhip = []
for i in range(stages):
    ratio = np.var(orders[i, 10:]) / np.var(customer_demand[10:])
    bullwhip.append(ratio)

st.subheader("📊 Bullwhip Ratios")
for i in range(stages):
    st.write(f"Stage {i+1}: {bullwhip[i]:.2f}")

# Plot demand vs orders
fig, ax = plt.subplots()
ax.plot(customer_demand, label="Customer Demand")
ax.plot(orders[0], label="Retailer Orders")
ax.plot(orders[1], label="Wholesaler Orders")
ax.plot(orders[2], label="Distributor Orders")
ax.plot(orders[3], label="Manufacturer Orders")
ax.legend()
st.pyplot(fig)

st.markdown("""
---

### Interpretation
Bullwhip Ratio > 1 indicates amplification.
Try reducing lead time or increasing information sharing.
""")
