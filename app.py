import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import io
import qrcode

st.title("📦 Bullwhip Effect – Interactive Model")

st.markdown("""
### Supply Chain Hierarchy  
Customer → Retailer → Wholesaler → Distributor → Manufacturer  

Orders move upstream.  
Demand information may or may not.
""")

# Sidebar controls
st.sidebar.header("Key Drivers of Bullwhip")

T = st.sidebar.slider("Time Periods", 150, 500, 300)
lead_time = st.sidebar.slider("Lead Time", 1, 8, 3)
alpha = st.sidebar.slider("Forecast Smoothing (α)", 0.01, 1.0, 0.4)
info_sharing = st.sidebar.checkbox("Information Sharing (All observe customer demand)")

np.random.seed(42)

mean_demand = 100
std_demand = 20
customer_demand = np.random.normal(mean_demand, std_demand, T)

stages = 4
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand
inventory_position = np.ones((stages, T)) * mean_demand * (lead_time + 1)

for t in range(1, T):
    for i in range(stages):
        
        # Demand seen by stage
        if i == 0:
            demand = customer_demand[t]
        else:
            demand = orders[i-1, t-1]
        
        # Forecast input
        if info_sharing:
            demand_for_forecast = customer_demand[t]
        else:
            demand_for_forecast = demand
        
        # Exponential smoothing
        forecast[i, t] = alpha * demand_for_forecast + (1 - alpha) * forecast[i, t-1]
        
        base_stock = forecast[i, t] * (lead_time + 1)
        
        # Order-up-to logic
        orders[i, t] = base_stock - inventory_position[i, t-1]
        
        # Update inventory position
        inventory_position[i, t] = (
            inventory_position[i, t-1] 
            + orders[i, t] 
            - demand
        )

# ---- Bullwhip Calculation ----

bullwhip = []
for i in range(stages):
    ratio = np.var(orders[i, 50:]) / np.var(customer_demand[50:])
    bullwhip.append(ratio)

st.subheader("📊 Bullwhip Ratio (Variance Amplification)")
st.markdown("""
**Bullwhip Ratio = Var(Stage Orders) / Var(Customer Demand)**  
Values > 1 indicate amplification.
""")

for i, name in enumerate(["Retailer", "Wholesaler", "Distributor", "Manufacturer"]):
    st.write(f"{name}: {bullwhip[i]:.2f}")

# ---- Plot 1: Time Series ----

fig1, ax1 = plt.subplots(figsize=(10,6))

ax1.plot(customer_demand, label="Customer Demand", linewidth=2)
ax1.plot(orders[0], label="Retailer Orders")
ax1.plot(orders[1], label="Wholesaler Orders")
ax1.plot(orders[2], label="Distributor Orders")
ax1.plot(orders[3], label="Manufacturer Orders")

ax1.set_title("Demand and Orders Over Time")
ax1.legend()
st.pyplot(fig1)

# ---- Plot 2: Bullwhip Bar Chart ----

fig2, ax2 = plt.subplots()

stage_names = ["Retailer", "Wholesaler", "Distributor", "Manufacturer"]

ax2.bar(stage_names, bullwhip)
ax2.axhline(1, linestyle="--")

ax2.set_title("Bullwhip Effect Across Supply Chain")
ax2.set_ylabel("Variance Ratio")

st.pyplot(fig2)