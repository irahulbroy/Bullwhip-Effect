import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(layout="wide")
st.title("📦 Bullwhip Effect Decision Lab")

TARGET = 1.5
SERVICE_TARGET = 0.95

st.header(f"🎯 Challenge: Reduce Bullwhip ≤ {TARGET} AND Maintain Service Level ≥ {int(SERVICE_TARGET*100)}%")
st.markdown("""
**Supply Chain:** Customer → Retailer → Wholesaler → Distributor → Manufacturer  
**Objective:** Find the optimal balance between system stability (low bullwhip) and customer responsiveness (high service level).
""")

# ---------------- Cached Demand Generation ---------------- #
# This ensures demand stays identical when widgets are toggled
@st.cache_data
def generate_demand(T, mean_demand):
    np.random.seed(42) # Fixed seed so all students face the exact same scenario
    std_demand = 30
    demand = np.random.normal(mean_demand, std_demand, T)
    
    # Introduce disruptive demand spikes
    for t in range(T):
        if np.random.rand() < 0.05: # 5% chance of a spike
            demand[t] *= np.random.uniform(1.5, 2.0)
    
    # Ensure no negative demand
    demand = np.maximum(demand, 0)
    return demand, std_demand

T = 400
mean_demand = 100
customer_demand, std_demand = generate_demand(T, mean_demand)

# ---------------- Sidebar Variables ---------------- #
st.sidebar.header("Decision Variables")
lead_time = st.sidebar.slider("Lead Time (L)", 2, 8, 4, help="Time periods between ordering and receiving.")
alpha = st.sidebar.slider("Forecast Responsiveness (α)", 0.05, 0.90, 0.40, help="Higher = reacts faster to recent demand. Lower = smooths out noise.")
order_multiplier = st.sidebar.slider("Order Cushioning (Shortage Gaming)", 1.0, 2.0, 1.3, help="Panic ordering multiplier when stock is low.")
safety_stock_multiplier = st.sidebar.slider("Safety Stock Multiplier (z)", 0.5, 3.0, 1.0, 0.1, help="Buffer against demand volatility.")
info_sharing = st.sidebar.checkbox("Enable Information Sharing", value=False, help="All stages can see the original customer demand.")

# ---------------- Simulation Setup ---------------- #
stages = 4
stage_names = ["Retailer", "Wholesaler", "Distributor", "Manufacturer"]

# Initialize tracking arrays
orders = np.zeros((stages, T))
forecast = np.ones((stages, T)) * mean_demand
on_hand = np.zeros((stages, T))
stockouts = np.zeros((stages, T))

# Static safety stock based on demand variance and lead time
# Formula: z * sigma * sqrt(L+1)
fixed_safety_stock = safety_stock_multiplier * std_demand * np.sqrt(lead_time + 1)

# Initialize steady state inventory
for i in range(stages):
    on_hand[i, 0] = fixed_safety_stock + (mean_demand * 1.5) # Modest starting buffer

# ---------------- Core Simulation Loop ---------------- #
for t in range(1, T):
    for i in range(stages):
        # 1. Realize Demand
        if i == 0:
            demand = customer_demand[t]
        else:
            demand = orders[i-1, t] # Immediate upstream order

        # 2. Receive Shipments (Lead Time Delay)
        if t >= lead_time:
            arriving_order = orders[i, t - lead_time]
        else:
            arriving_order = mean_demand 

        # 3. Update physical inventory
        on_hand[i, t] = on_hand[i, t-1] + arriving_order - demand

        # 4. Check Stockouts (Lost Sales model)
        if on_hand[i, t] < 0:
            stockouts[i, t] = 1
            on_hand[i, t] = 0 # Cannot have negative physical boxes

        # 5. Forecasting (Information sharing bypasses local demand)
        demand_for_forecast = customer_demand[t] if info_sharing else demand
        forecast[i, t] = alpha * demand_for_forecast + (1 - alpha) * forecast[i, t-1]

        # 6. Calculate Pipeline Inventory (goods in transit)
        pipeline_inventory = np.sum(orders[i, max(0, t - lead_time):t])
        inventory_position = on_hand[i, t] + pipeline_inventory

        # 7. Order Generation (Base Stock Policy)
        # Target = Expected demand over Lead Time + Safety Stock
        target_base_stock = (forecast[i, t] * (lead_time + 1)) + fixed_safety_stock
        
        raw_order = max(target_base_stock - inventory_position, 0)
        
        # Apply shortage gaming (panic ordering) if inventory position is low
        if raw_order > mean_demand:
            raw_order *= order_multiplier
            
        orders[i, t] = raw_order

# ---------------- Metrics Calculation ---------------- #
# Discard the first 100 periods as "warm up" to avoid initial state bias
burn_in = 100
bullwhip = [np.var(orders[i, burn_in:]) / np.var(customer_demand[burn_in:]) for i in range(stages)]
service_levels = 1 - stockouts[:, burn_in:].mean(axis=1)

# ---------------- Dashboard UI ---------------- #
st.subheader("📊 Performance Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Bullwhip Ratios (Target ≤ 1.5)")
    for i in range(stages):
        if bullwhip[i] > TARGET:
            st.markdown(f":red[**{stage_names[i]}: {bullwhip[i]:.2f}** ⚠]")
        else:
            st.markdown(f":green[**{stage_names[i]}: {bullwhip[i]:.2f}** ✅]")

with col2:
    st.markdown(f"### Service Levels (Target ≥ {int(SERVICE_TARGET*100)}%)")
    for i in range(stages):
        if service_levels[i] < SERVICE_TARGET:
            st.markdown(f":red[**{stage_names[i]}: {service_levels[i]*100:.1f}%** ⚠]")
        else:
            st.markdown(f":green[**{stage_names[i]}: {service_levels[i]*100:.1f}%** ✅]")

# Challenge Status Evaluation
success = all(r <= TARGET for r in bullwhip) and all(s >= SERVICE_TARGET for s in service_levels)
st.markdown("---")
if success:
    st.success("🏆 **Challenge Completed!** You successfully balanced efficiency and responsiveness.")
else:
    st.warning("⚠ **System Unstable or Unresponsive.** Review your trade-offs between buffering and forecasting.")

# ---------------- Visualizations ---------------- #
st.markdown("### Order Amplification Visualization")
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
fig, axs = plt.subplots(2, 2, figsize=(16, 8), sharey=True)
axs = axs.flatten()

for i in range(stages):
    # Plot Customer Demand as baseline
    axs[i].plot(customer_demand[burn_in:], color="black", alpha=0.3, label="Customer Demand")
    # Plot Stage Orders
    axs[i].plot(orders[i, burn_in:], label=f"{stage_names[i]} Orders", color=colors[i], linewidth=2)
    
    axs[i].set_title(f"{stage_names[i]} Variance", fontsize=12)
    axs[i].legend(loc="upper left")
    axs[i].grid(True, alpha=0.3)

plt.tight_layout()
st.pyplot(fig)# ---------------- Visualizations ---------------- #
st.markdown("### Order Amplification Visualization")
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

# 1. Increased figsize for a much larger overall plot canvas
fig, axs = plt.subplots(2, 2, figsize=(20, 14), sharey=True)
axs = axs.flatten()

for i in range(stages):
    # 2. Thicker lines (linewidth=3) for better visibility
    axs[i].plot(customer_demand[burn_in:], color="black", alpha=0.3, label="Customer Demand", linewidth=3)
    axs[i].plot(orders[i, burn_in:], label=f"{stage_names[i]} Orders", color=colors[i], linewidth=3)
    
    # 3. Larger titles and axis labels
    axs[i].set_title(f"{stage_names[i]} Variance", fontsize=22, fontweight='bold')
    axs[i].set_ylabel("Units", fontsize=18)
    axs[i].set_xlabel("Time Period", fontsize=18)
    
    # 4. Larger tick marks on the axes
    axs[i].tick_params(axis='both', which='major', labelsize=16)
    
    # 5. Larger legend text
    axs[i].legend(loc="upper left", fontsize=16)
    axs[i].grid(True, alpha=0.4)

# Adjust layout so the larger text doesn't overlap
plt.tight_layout(pad=3.0)
st.pyplot(fig)