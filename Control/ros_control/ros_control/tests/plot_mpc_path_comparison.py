import pathlib
import matplotlib.pyplot as plt


def fabricate_paths():
    desired = [
        (0.0, 0.0),
        (0.6, 0.1),
        (1.3, 0.3),
        (2.1, 0.7),
        (3.0, 1.2),
        (4.0, 1.8),
        (5.0, 2.2),
        (6.0, 2.4),
        (7.0, 2.5),
        (8.0, 2.6),
        (9.0, 2.7),
    ]

    predicted = [
        (0.0, 0.0),
        (0.7, 0.15),
        (1.4, 0.35),
        (2.2, 0.8),
        (3.1, 1.35),
        (4.1, 1.95),
        (5.1, 2.35),
        (6.1, 2.55),
        (7.1, 2.7),
        (8.1, 2.85),
        (9.1, 3.0),
    ]
    return desired, predicted


def _save(desiredPath, predictedPath, name:str):

    desired_x = [v[0] for v in desiredPath]
    desired_y = [v[1] for v in desiredPath]

    predicted_x = [v[0] for v in predictedPath]
    predicted_y = [v[1] for v in predictedPath]

    max_coord = max(max(max(desired_x),max(desired_y)),max(max(predicted_x),max(predicted_y)))
    min_coord = min(min(min(desired_x),min(desired_y)),min(min(predicted_x),min(predicted_y)))


    fig, ax = plt.subplots()
    # plot the 2 lines
    ax.plot(desired_x,desired_y, "o-", label="Desired")
    ax.plot(predicted_x,predicted_y, "o-", label="Predicted")

    #highlight beginning and end
    ax.plot(desired_x[0], desired_y[0], 'go', markersize=12, label="Start")
    ax.plot(desired_x[-1], desired_y[-1], 'ro', markersize=12, label="End")

    ax.plot(predicted_x[0], predicted_y[0], 'go', markersize=12)
    ax.plot(predicted_x[-1], predicted_y[-1], 'ro', markersize=12)

    ax.set_title(name)
    
    all_x = desired_x + predicted_x
    all_y = desired_y + predicted_y

    center_x = (min(all_x) + max(all_x)) / 2
    center_y = (min(all_y) + max(all_y)) / 2
    span_x = max(all_x) - min(all_x)
    span_y = max(all_y) - min(all_y)
    padding = 1.0
    side_length = max(span_x, span_y) + 2 * padding

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(center_x - side_length / 2, center_x + side_length / 2)
    ax.set_ylim(center_y - side_length / 2, center_y + side_length / 2)
    #ax.set_xlim(min_coord-1, max_coord+1)
    #ax.set_ylim(min_coord-1, max_coord+1)
    ax.legend()

    filepath = plot_dir / f"{name.replace(' ', '_')}.png"
    fig.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.close(fig)
    print(f"\nPlot saved: {filepath}")




"""def save_plot(output_path: str = "test_plots/mpc_path_comparison.png"):
    desired, predicted = fabricate_paths()
    desired_x = [p[0] for p in desired]
    desired_y = [p[1] for p in desired]
    predicted_x = [p[0] for p in predicted]
    predicted_y = [p[1] for p in predicted]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(desired_x, desired_y, color="tab:blue", marker="o", linewidth=2.5, label="Desired path")
    ax.plot(predicted_x, predicted_y, color="tab:orange", marker="x", linewidth=2.0, label="Predicted path")

    ax.set_title("MPC path optimisation example")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.legend()

    output = pathlib.Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved plot to {output.resolve()}")
"""

if __name__ == "__main__":
    plot_dir = pathlib.Path("test_plots")
    plot_dir.mkdir(exist_ok=True)
    desired, predicted  = fabricate_paths()
    _save(desired,predicted, "Curved")
