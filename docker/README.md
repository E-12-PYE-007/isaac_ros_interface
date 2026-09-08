# Isaac ROS dependency layers

Custom Docker layers adding package-specific dependencies for the NVIDIA Isaac
ROS modules this workspace uses. They stack on top of the stock `ros2_humble`
Isaac ROS dev image.

## 1. What the Dockerfiles do

| Layer | Adds |
|-------|------|
| `dockerfiles/Dockerfile.nvblox_deps` | `ros-humble-isaac-ros-nvblox` (nvblox runtime) |
| `dockerfiles/Dockerfile.visual_slam_deps` | Isaac ROS Visual SLAM / cuVSLAM runtime deps (GXF packages) + `magic_enum` built from source (apt package is broken) |

`setup/.isaac_ros_common-config` selects the combined image key
`ros2_humble.visual_slam_deps.nvblox_deps` and points the layer build at
`dockerfiles/`.

## 2. Setup (fresh machine)

Needs `git`, `git-lfs`, Docker. Run:

    src/aion_vslam/docker/setup/setup.sh

Clones the pinned upstream repos (`isaac_ros_common`, `isaac_ros_visual_slam`)
next to `aion_vslam/` and copies the config into `isaac_ros_common/scripts/`.

## 3. Running the container (day to day)

    src/isaac_ros_common/scripts/run_dev.sh

First run builds the layered image; later runs reuse or attach to the running
container. Build the workspace with `colcon build` inside it as usual.
