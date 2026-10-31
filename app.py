import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from collections import deque

# --- 1. SIDEBAR UI CONTROLS ---
st.sidebar.title("Simulation Controls")
G = st.sidebar.slider("Gravity (G)", 0.1, 5.0, 1.0, 0.1)
step_per_sec = st.sidebar.number_input("Steps per Second", 100, 20000, 10000)
simulation_time = st.sidebar.number_input("Total Sim Time (s)", 10, 200, 65)

st.sidebar.subheader("Performance Settings")
# Fixes the jagged lines: Save a point to the trail frequently
trail_density = st.sidebar.slider("Trail Smoothness (Steps per save)", 1, 50, 10)
# Fixes the framerate: Update the screen less frequently
render_frequency = st.sidebar.slider("Steps between UI frames", 100, 2000, 400)
# Prevents browser memory overload
max_trail = st.sidebar.slider("Max Trail Length", 50, 1000, 300)

st.sidebar.subheader("Asteroid Starting State")
start_x = st.sidebar.number_input("Start X", -5.0, 5.0, 2.0)
start_y = st.sidebar.number_input("Start Y", -5.0, 5.0, 3.0)
start_vx = st.sidebar.number_input("Start Velocity X", -5.0, 5.0, 0.0)
start_vy = st.sidebar.number_input("Start Velocity Y", -5.0, 5.0, 0.0)

planets = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0]])


# --- 2. THE GENERATOR FUNCTION ---
def simulate_live():
    dt = 1 / step_per_sec
    total_steps = simulation_time * step_per_sec
    collision_thresh_sq = 0.01**2

    curr_pos = np.array([start_x, start_y])
    curr_vel = np.array([start_vx, start_vy])

    diffs = planets - curr_pos
    dist_sq = np.sum(diffs**2, axis=1)
    dist = np.sqrt(dist_sq)
    curr_accel = np.sum((G / dist_sq)[:, None] * (diffs / dist[:, None]), axis=0)

    trail_x = deque(maxlen=max_trail)
    trail_y = deque(maxlen=max_trail)

    i = 0
    while True:
        # Velocity Verlet Math
        curr_pos = curr_pos + (curr_vel * dt) + (0.5 * curr_accel * dt**2)
        diffs = planets - curr_pos
        dist_sq = np.sum(diffs**2, axis=1)

        if np.any(dist_sq <= collision_thresh_sq):
            yield trail_x, trail_y, curr_pos, "Collision Detected!"
            return

        dist = np.sqrt(dist_sq)
        new_accel = np.sum((G / dist_sq)[:, None] * (diffs / dist[:, None]), axis=0)
        curr_vel = curr_vel + 0.5 * (curr_accel + new_accel) * dt
        curr_accel = new_accel

        # 1. Update the trail data frequently so the curve is physically accurate and smooth
        if i % trail_density == 0:
            trail_x.append(curr_pos[0])
            trail_y.append(curr_pos[1])

        # 2. Yield to the UI less frequently so the browser has time to render
        if i % render_frequency == 0:
            yield trail_x, trail_y, curr_pos, "Running..."
        i+=1


# --- 3. STREAMLIT APP LAYOUT ---
st.title("Web-Native Fast Gravity Dashboard")
status_text = st.empty()
plot_placeholder = st.empty()

if st.button("Start Simulation"):

    # Pre-build the static planet layer once
    planet_df = pd.DataFrame({"x": planets[:, 0], "y": planets[:, 1]})
    planet_chart = (
        alt.Chart(planet_df)
        .mark_circle(size=250, color="red")
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-4, 4]), title="X Coordinate"),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-4, 4]), title="Y Coordinate"),
        )
    )

    for trail_x, trail_y, curr_pos, status in simulate_live():
        status_text.text(status)

        # Build the trail layer (We must assign an 'order' column so Altair connects
        # the dots chronologically, otherwise it sorts them left-to-right by X coordinate)
        trail_df = pd.DataFrame(
            {"x": trail_x, "y": trail_y, "order": range(len(trail_x))}
        )
        trail_chart = (
            alt.Chart(trail_df)
            .mark_line(color="blue", opacity=0.4, strokeWidth=2)
            .encode(x="x:Q", y="y:Q", order="order:Q")
        )

        # Build the asteroid head layer
        asteroid_df = pd.DataFrame({"x": [curr_pos[0]], "y": [curr_pos[1]]})
        asteroid_chart = (
            alt.Chart(asteroid_df)
            .mark_circle(size=120, color="blue")
            .encode(x="x:Q", y="y:Q")
        )

        # Layer them together into a single JSON payload
        final_chart = alt.layer(planet_chart, trail_chart, asteroid_chart).properties(
            width=700, height=700
        )

        # Overwrite the placeholder instantly using web rendering
        plot_placeholder.altair_chart(final_chart, use_container_width=True)
