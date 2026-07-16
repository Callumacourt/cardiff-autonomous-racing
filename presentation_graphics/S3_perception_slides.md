# Perception section — FS-AI 2026 Autonomous Design (S3)

Perception + localisation slice of the team's 30-minute presentation.
Budget: ~10 minutes for 8 slides, leaving room for the other modules.
Visual-heavy by design: every mechanism diagram is paired with real
evidence that it actually ran — nothing is asserted without a picture
backing it. Graphics referenced below are in this folder.

Judging criteria these slides hit (S3.6.2): software architecture, sensor
selection & integration, hybrid ML/theoretical approach, algorithm structure,
simulation test evidence (S3.5.3).

---

## Slide 1 — "Perception takes in X, outputs Y"  (~0.5 min)

**Graphic:** `0_inputs_outputs.png`, full slide — plain black-box view,
no internals

**Layout:** As bare as the deck gets on purpose: three input boxes, one
black "PERCEPTION" box, two output boxes, arrows between them. No bullets
needed — this slide is entirely spoken. Internals are deliberately withheld
for slide 2.

Speaker notes:
> So — perception takes in camera, IMU, and velocity, and outputs two
> things: the car's position, and the cone map. That's the whole module
> from the outside. Next slide, we open the box.

---

## Slide 2 — "We publish two things: a pose and a map"  (~1 min)

**Graphic:** `1_pipeline.png` (full width, ~70% of slide)

**Layout:** Small title top-left. Pipeline diagram dominates. 3-4 bullets
below it in a single row or tight block. Sets up the three topics that
follow — the only pure-diagram slide in the deck, everything after this
pairs a mechanism with proof.

Bullets:
- One job: turn a stereo camera into "where is the car" + "where are the cones"
- Three ROS2 nodes, one topic each: detection → localisation → mapping
- Everything downstream consumes just two outputs: pose + cone map

Speaker notes:
> Perception's contract with the rest of the car is deliberately narrow: we
> publish a pose and a cone map, nothing else. The next few slides walk
> through each part — and for each one, we'll show it actually running,
> not just explain it.

---

## Slide 3 — "This is what the car sees"  (~1 min)

**Graphic:** `9_yolo_live_frame.png` — full slide, real unedited detector
output, minimal text over it

**Layout:** Let the image do the work. Title only, maybe one caption line
underneath (already baked into the image). No bullets — this slide's job
is a hook, not information density. This is the strongest single visual in
the deck; don't compete with it.

Speaker notes:
> Before we talk about how this works, here's what it actually looks like
> running — this is a real, unedited frame from the detector mid-lap, boxes
> and coordinates as published. Orange, blue, and yellow cones, each with a
> confidence score and a 3D position already computed. Everything on the
> next few slides is what turns this into a car that can navigate.

---

## Slide 4 — Topic: Cone Detection — "Learning turns pixels into cones"  (~1.5 min)

**Graphic:** `6_cone_detection_flow.png` (full width, ~60% of slide)

**Layout:** Diagram across the top, bullets below in two short groups: "how
it works" and "what it runs on". This slide explains the mechanism behind
the frame you just showed on slide 3 — say that transition out loud.

Bullets:
- YOLOv8 single-stage detector, fine-tuned on FS cone classes (blue /
  yellow / orange / large-orange / unknown), per-box confidence retained
- 2D→3D: pinhole projection of box centre using depth Z and intrinsics
  (fx, fy, cx, cy) from CameraInfo — not an approximation, the calibrated
  camera model
- Depth sampled at 65% of box height (5×5 median-filtered patch), not the
  centroid — avoids background bleed-through on distant/occluded cones
- Sensor: stereo depth from the stock ZED2, camera-only — sufficient at
  the ≤15 m operating range this task needs, avoids LiDAR integration
  overhead on a shared vehicle
- Confidence is a first-class field: propagates through PointCloud2 into
  EKF observation weighting and mapper promotion, not just detection

Speaker notes:
> This is the mechanism behind the frame on the last slide. It's the only
> learned component in the stack — everything from here on is classical
> estimation, no neural network involved. The 2D-to-3D step is calibrated
> pinhole projection, not a heuristic — we use the camera's actual
> intrinsics from CameraInfo. Confidence isn't discarded after detection;
> it's carried as a number all the way to the map-promotion threshold.

---

## Slide 5 — Topic: Localisation — "Re-seeing a known cone corrects the car's position"  (~2 min)

**Graphic:** `7_slam_predict_update.png` as the main diagram; `10_slam_map_result.png`
as a smaller inset or split-screen, pointing specifically at the red
dashed trajectory line

**Layout:** This is the technically densest slide (it's what S3.6.2 is
scoring most directly) — give it the most room of the eight. Diagram on
one side, real trajectory result on the other, so the mechanism and its
proof are on screen together. Keep the diagram itself intuitive (predict/
update boxes, no equations on it) — it's read at a glance from the back of
the room; the equations and complexity numbers belong in the bullets and
your delivery, where you control the pace.

Bullets:
- State: x = [xᵣ, yᵣ, θᵣ, x₁, y₁, ..., xₙ, yₙ]ᵀ — pose + every landmark, one
  joint vector, dimension 3+2n; covariance P tracks pose-pose, pose-landmark
  and landmark-landmark correlation
- PREDICT: unicycle motion model (v from wheel speed, ω from IMU),
  linearised via a 3×3 Jacobian Fx; covariance propagated only on the pose
  block + pose-landmark cross-terms, scaled by process noise Q·dt
- UPDATE: per-landmark Jacobians in block form (Aᵢ: 2×3 pose block, Bᵢ:
  2×2 landmark block); innovation covariance S built directly from the
  relevant P sub-blocks — no dense H ever formed
- Data association: Mahalanobis-gated nearest-neighbour match; unmatched
  detections initialise new landmarks
- Correction: Kalman gain from block products, Joseph-form covariance
  update for numerical stability under repeated corrections
- Complexity: refactored from dense O(n³) predict/update to block-structured
  O(n) predict / O(n²) update — regression-tested bit-for-bit equivalent
  to the naive dense formulation
- Right: the real result — estimate (dashed) vs. ground truth (solid),
  one validated lap

Speaker notes:
> The state vector holds the car and the map together — that shared
> covariance is exactly why re-observing a cone corrects the car's
> position, not just the landmark's. Concretely: predict only touches the
> 3×3 pose block and the pose-landmark cross-covariance; update computes
> per-landmark Jacobians directly from the relevant covariance sub-blocks
> instead of building a dense observation matrix. The payoff is complexity:
> the naive formulation is cubic in map size, and our node was falling
> behind the IMU at around 40 landmarks. We restructured the update into
> block form, verified it against the dense implementation with a
> regression test to confirm identical output, and it's been real-time at
> full-track map size since. And this isn't theoretical — this is the
> actual estimated path against actual ground truth from one validated lap.

---

## Slide 6 — Topic: Cone Mapping — "Nothing reaches the map on one sighting"  (~1.5 min)

**Graphic:** `8_cone_mapper_flow.png` as the main diagram; `10_slam_map_result.png`
reused, this time pointing at the filled cone dots (the built map) rather
than the trajectory line

**Layout:** Same split treatment as slide 5 — diagram plus the same real
result image, different focus. Reusing one honest piece of evidence for
two related claims is fine; say explicitly it's the same lap's result.

Bullets:
- SE(2) transform of each camera-frame detection into world coordinates
  using the current SLAM pose estimate
- Plausibility gate: reject detections outside a physically valid height
  band — defence-in-depth against bad depth samples upstream
- Probation buffer: promotion requires an N-of-M re-sighting count +
  confidence threshold; orange cones held to a stricter bar (rarer,
  higher cost if wrong)
- Promoted cones refine position on every re-sighting via an exponential
  moving average — recent observations weighted more than stale ones
- Publishes confidence ≥ 0.3 to `/cone_map/local` (planner feed);
  unfiltered map retained on `/cone_map/global` for diagnostics
- Right: the actual built map from that same lap — 65/67 track cones,
  filled dots against true positions (open circles)

Speaker notes:
> Same picture as last slide, different focus — now look at the dots
> rather than the line. Every filled marker went through the probation
> buffer: an N-of-M re-sighting count plus a confidence floor before
> anything is trusted, and even after promotion, position keeps refining
> via an EMA rather than being frozen at first detection. That's why the
> built map lines up this tightly with the true track layout — it's not
> one lucky frame, it's convergence over the whole lap.

---

## Slide 7 — "0.67m RMSE, measured, not claimed"  (~1 min)

**Graphic:** `3_slam_error_over_lap.png`, full width

**Layout:** Your "read from the back of the room" slide. The three
headline numbers should be large enough to read before anyone parses a
bullet — put them as big tabular text near the top if your template allows,
not buried in a list.

Bullets:
- Automated regression test: full autonomous lap in EUFS sim vs ground truth
- Position RMSE 0.67 m · mean heading error 1.1° · 65/67 cones (97%) · 0 false cones
- Loop closure visible: drift peaks ~1.4 m on unmapped track, snaps back
  when start-line cones are re-recognised — slide 5's UPDATE step, proven

Speaker notes:
> This is our simulation test data, required by the rules and the backbone
> of how we validate every change. The lap is driven by a test-only driver
> on the ground-truth centerline, so we're testing perception in isolation.
> This curve is the localisation story from slide 5 in one picture: drift
> grows through unmapped track, then collapses at loop closure. This test
> runs as one command — no change ships to perception without a lap.

---

## Slide 8 — "This is the real data downstream consumers receive"  (~1 min, handover slide)

**Graphic:** `5_planner_view.png` (full width — already a two-panel graphic)

**Layout:** Keep this one visually calmer than slide 7 — it's a handover,
not a climax. Bullets stay short; your last line should be spoken ("over
to path planning"), not read off the slide.

Bullets:
- Lap 1: Path Planning drives on `/cone_map/local` (live, confidence-
  filtered) — midpoint-between-cones path while the track is still being
  discovered
- Lap 2 onward: Path Planning switches to `/cone_map/global` — the
  now-complete track map — to run Global Trajectory Optimisation for the
  racing line
- `/odometry/slam` is consumed by both: Path Planning for localisation,
  and Control directly for its MPC vehicle state (pose + velocity)
- Real-car deltas are launch parameters only: ZED2 wrapper topics,
  /ros_can/imu, measured camera offset — same code, not a rewrite
- Open item we own: no signal yet for "map is stable, safe to trigger
  GTO" — next on our list, flagged rather than hidden

Speaker notes:
> This is the literal data downstream receives — real messages captured
> mid-lap, not a schematic. Two consumers, not one: Path Planning reads
> our local map for lap 1 and our global map from lap 2 onward once the
> track is fully mapped, and Control reads our pose directly for its own
> control loop, independent of Path Planning. Everything sim-specific is a
> launch parameter, so the code that drove the validated laps is the code
> that goes on the car. And we're upfront about what's not built yet: a
> map-stable signal Path Planning needs to know exactly when to trust the
> global map. Hand over to path planning.

---

## Q&A bank (perception questions judges are likely to ask)

- **Why not LiDAR?** Stereo depth is sufficient at cone ranges; camera-only
  halves integration on a shared vehicle. LiDAR is the natural upgrade for
  range + lighting robustness.
- **Why EKF over particle filter / graph SLAM?** Landmark count is small
  (~70), Gaussian assumptions hold, and EKF gives a per-timestep inspectable
  state. Graph SLAM pays off at map sizes we never reach.
- **Data association failures?** Mahalanobis gating; wrong-association is
  the classic EKF-SLAM failure mode — not observed across validated laps,
  helped by colour as a hard constraint.
- **What's your position error budget?** Track lanes are ~3 m wide at
  minimum; 0.67 m RMSE keeps the car in-lane with margin; heading error ~1°.
- **How do you know the sim transfers?** We don't claim it fully does —
  identical code path and message contracts are proven; sensor realism
  (lighting, depth noise) is the known gap, stated openly.
- **IMU on the camera or the vehicle?** Vehicle's own IMU via /ros_can/imu
  on the real car (yaw rate is mount-position independent on a rigid body);
  sim IMU plugin in EUFS. Topic is a launch parameter.
- **Cone map colours wrong / unknown cones?** Planner contract: blue=left,
  yellow=right, orange and unknown are excluded from boundary logic.
- **Is that map result the best-case run, or typical?** Say plainly which
  it is before a judge asks — if it's your best validated lap, own that,
  and state the regression test runs this way every time, not cherry-picked
  for the deck.
