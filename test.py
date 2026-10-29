import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#physical constant
G = 0.1 #gravitational constant

#timing parameters
simulation_time = 300
step_per_sec = 1000
play_speed = 20


collision_accuracy = 0.01

dt = 1 / step_per_sec

#initial object values
planets = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0]])
asteroid_start_pos = (2.0, 2.0)
asteroid_start_vel = (0.0, 0.0)


def simulate():
    total_steps = simulation_time * step_per_sec
    positions = np.zeros((total_steps, 2))

    curr_pos = np.array(asteroid_start_pos)
    curr_vel = np.array(asteroid_start_vel)
    collision_thresh_sq = collision_accuracy**2


    diffs = planets - curr_pos
    dist_sq = np.sum(diffs**2, axis=1)
    dist = np.sqrt(dist_sq)
    force = G / dist_sq
    curr_accel = np.sum(force[:, None] * (diffs / dist[:, None]), axis=0)

    for i in range(total_steps):
        positions[i] = curr_pos

        # Update position using current velocity and acceleration
        # Formula: p(t+dt) = p(t) + v(t)*dt + 0.5*a(t)*dt^2
        curr_pos = curr_pos + (curr_vel * dt) + (0.5 * curr_accel * dt**2)

        #  Get vectors and distances for the new position
        diffs = planets - curr_pos
        dist_sq = np.sum(diffs**2, axis=1)

        # Collision check
        if np.any(dist_sq <= collision_thresh_sq):
            hit_index = np.argmin(dist_sq)
            return positions[: i + 1]

        #  Calculate new acceleration
        dist = np.sqrt(dist_sq)
        force = G / dist_sq
        new_accel = np.sum(force[:, None] * (diffs / dist[:, None]), axis=0)

        # Update velocity using the average of old and new accelerations
        # Formula: v(t+dt) = v(t) + 0.5 * (a(t) + a(t+dt)) * dt
        curr_vel = curr_vel + 0.5 * (curr_accel + new_accel) * dt

        curr_accel = new_accel

    return positions


def main():
    positions = simulate()

    fig, ax = plt.subplots()

    x_spec = planets[:, 0]
    y_spec = planets[:, 1]
    ax.scatter(x_spec, y_spec, color="red", label="Planets", s=50)

    #  Create empty line/point objects that we will update in the animation
    (trail_line,) = ax.plot([], [], "b-", alpha=0.4, linewidth=1, label="Trail")
    (asteroid_point,) = ax.plot([], [], "bo", markersize=1, label="Asteroid")

    margin = 0.5
    ax.set_xlim(np.min(positions[:, 0]) - margin, np.max(positions[:, 0]) + margin)
    ax.set_ylim(np.min(positions[:, 1]) - margin, np.max(positions[:, 1]) + margin)

    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_title("Gravity Simulation Animation")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_aspect("equal", adjustable="box")

    frame_skip = int(step_per_sec*play_speed/100) 
    total_frames = len(positions) // frame_skip

    def update(frame):
        idx = frame * frame_skip

        trail_line.set_data(positions[:idx, 0], positions[:idx, 1])

        asteroid_point.set_data([positions[idx, 0]], [positions[idx, 1]])

        return trail_line, asteroid_point


    ani = animation.FuncAnimation(
        fig, update, frames=total_frames, interval=10, blit=True
    )

    plt.show()


if __name__ == "__main__":
    main()
