# Vision Guide — classical OpenCV box detection

> **ملخص عربي:** الكاميرا ثابتة فوق نقطة الالتقاط، وبتشوف الصندوق بخوارزمية بسيطة: فصل الصندوق عن السير بلونه، وبعدين نلاقي حدوده ونحسب مركزه وزاويته. مفيش deep learning — الصندوق شكله ثابت والسير لونه مختلف، فالحل الكلاسيكي كفاية وأسرع وأوثق.

## 1. Status

The vision code lives in the `ar4_palletizing` package (`vision_node.py` +
`vision_utils.py`). This guide describes the pipeline it implements, so the
camera, the code and the calibration are set up consistently.

## 2. Setup — eye-to-hand

- **Camera:** one fixed USB camera, mounted above the pick point, looking
  straight down at the conveyor. This is called **eye-to-hand**: the camera
  does not move with the robot, it watches the workspace.
- **What is fixed:** the camera position, the conveyor position, the lighting,
  and the pick point. The only thing that changes is where the box stops on
  the belt.
- **Why fixed camera:** one calibration gives the camera→base transform
  forever. A camera on the arm (eye-in-hand) would need the transform
  recomputed for every arm pose.
- **Lighting:** keep it fixed (same lamps, no daylight changes). The whole
  pipeline below depends on stable lighting — if the light changes, the
  threshold in step 2 stops working.

## 3. The pipeline (classical OpenCV only)

Input: one colour frame from `/camera/image_raw`.
Output: box centre + rotation angle, as a `PoseStamped` in the robot base frame.

```text
frame (BGR)
  │  1. cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  ▼
grayscale
  │  2. cv2.threshold(gray, T, 255, cv2.THRESH_BINARY_INV)
  │     (T = threshold value, tuned once on the real conveyor)
  ▼
binary image: box = white, conveyor = black
  │  3. cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  ▼
contours
  │  4. keep the largest contour by area; reject the rest
  │     (filters out noise, labels, small objects on the belt)
  ▼
box contour
  │  5. cv2.minAreaRect(contour)  →  ((cx, cy), (w, h), angle)
  ▼
centre (cx, cy) in pixels + rotation angle
  │  6. convert pixels → metres (calibration, section 4)
  │     + static camera→base transform (TF)
  ▼
PoseStamped in base frame  →  /box_pose  →  palletizing node
```

### Step-by-step notes

1. **Grayscale.** Colour is not needed — the box and the conveyor differ in
   brightness, so one channel is enough.
2. **Threshold.** Pick the threshold `T` once, on the real setup, by looking
   at the binary image: the box must be solid white and the belt solid black.
   Use `THRESH_BINARY_INV` if the box is darker than the belt, plain
   `THRESH_BINARY` if it is lighter. If the belt and the box are close in
   brightness, change the belt colour / add a contrasting mat — do not try to
   fix it in code.
3. **Contours.** `RETR_EXTERNAL` takes only outer contours (the box outline),
   which is all we need.
4. **Largest contour.** The box is the biggest bright object in the frame.
   Reject contours smaller than a minimum area (noise) — the minimum area
   depends on the real box size, still TBD.
5. **`minAreaRect`.** Returns the smallest rotated rectangle around the
   contour: centre `(cx, cy)`, size `(w, h)`, and rotation `angle`. The angle
   tells the gripper how to rotate (`joint_6` / wrist) so the fingers close
   along the box sides instead of across a corner. Note: OpenCV's angle
   convention for `minAreaRect` is awkward (angle range and which side is
   `w` flip at 90°) — test it with a box at a known angle and normalise it
   in code before using it.
6. **Pixels → metres + TF.** See section 4.

### What the code needs (per step)

| Step | OpenCV function | Tuned value |
|---|---|---|
| Grayscale | `cv2.cvtColor` | — |
| Threshold | `cv2.threshold` | `T` — tune once on the real conveyor |
| Contours | `cv2.findContours` | minimum contour area — tune to the real box size |
| Rectangle | `cv2.minAreaRect` | angle normalisation — test with a known angle |
| ROS bridge | `cv_bridge` (`CvBridge().imgmsg_to_cv2`) | — |

## 4. Camera calibration

Two calibrations are needed:

1. **Intrinsic calibration** (the camera itself): focal length, principal
   point, distortion. Do it once with a checkerboard and the ROS 2 camera
   calibration tool (`ros2 run camera_calibration cameracalibrator`). Save the
   result — it is used to undistort every frame.
2. **Hand–eye calibration** (camera → robot base): the static transform
   between `camera_link` and `base_link` (or `world`). Because the camera is
   fixed, this is a single static transform published once (e.g. in the URDF
   or a `static_transform_publisher`). Measure it after mounting the camera:
   put a known object at a known base-frame position, read its pixel position,
   and solve for the transform. A practical shortcut is an **ArUco marker
   placed at a known position on the conveyor** — detect it once, and the
   transform falls out of the detection.

For a top-down camera at a fixed height, the pixel→metre conversion is a
simple scale (metres per pixel) plus the transform — no full 3D reconstruction
is needed, because every box sits on the same belt plane.

## 5. ArUco option

If the box detection ever proves unreliable (e.g. the belt colour changes, or
boxes of different sizes appear), the fallback is **ArUco markers**:

- Stick one ArUco marker on each box (or on the belt at the pick point).
- Detect with `cv2.aruco.detectMarkers` — it returns the marker's centre and
  corners directly, with no threshold tuning.
- ArUco also gives orientation, and the marker ID can identify which box
  (or which pallet slot) it belongs to.

ArUco is the backup plan, not the first plan — threshold + contours is
simpler and needs nothing stuck to the boxes.

## 6. Why no deep learning

Deep learning (e.g. a pretrained YOLO) is **not needed** for this project,
and the team has agreed on classical OpenCV. Reasons:

- **One object, one shape.** There is a single box type, very small, with a
  fixed rectangular shape. A detector trained to find "any box" is overkill
  for "this box".
- **Contrasting background.** The box sits on a conveyor of a different
  colour, under fixed lighting. Thresholding separates them reliably.
- **No clutter.** One box at a time at the pick point, nothing else in the
  frame. There is nothing for a neural network to disambiguate.
- **Deterministic and debuggable.** A threshold value and a contour area can
  be inspected, tuned and explained. A network's failure mode is a black box.
- **Runs anywhere.** The pipeline runs on the laptop CPU at full camera rate
  with no GPU and no model files.

Reconsider a pretrained YOLO **only if** the setup changes: several box types
or sizes, cluttered belt, or lighting that cannot be fixed. Until then,
classical OpenCV is the agreed approach.

## 7. What to verify first (checklist)

- [ ] Camera mounted above the pick point, looking straight down, fixed
- [ ] Lighting fixed; binary image shows a solid white box on a solid black belt
- [ ] Largest contour is the box (not a belt seam, label or shadow)
- [ ] `minAreaRect` angle matches a box placed at a known angle
- [ ] Pixel→metre scale measured (place a ruler / known-size box on the belt)
- [ ] Camera→base transform measured and published as a static TF
- [ ] `/box_pose` in the base frame matches the real box position (check with
      a tape measure: put the box at a known spot, compare with the published pose)
