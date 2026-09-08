#!/usr/bin/env bash
#
# One-time bootstrap for a fresh machine.
#
#   * clones the pinned NVIDIA Isaac ROS upstream repos as siblings of aion_vslam/
#   * copies the layer-build config into isaac_ros_common/scripts/
#
# Run from anywhere:  src/aion_vslam/docker/setup/setup.sh
# Then:               src/isaac_ros_common/scripts/run_dev.sh

set -euo pipefail

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AION_DIR="$(cd "$SETUP_DIR/../.." && pwd)"   # .../src/aion_vslam
SRC_DIR="$(cd "$AION_DIR/.." && pwd)"        # .../src

# name | url | pinned commit (tip of release-3.2 as of this workspace)
REPOS=(
  "isaac_ros_common|https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common.git|fcf4d9e17f8f0a7f47f1d22d6a18421ce3768c01"
  "isaac_ros_visual_slam|https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_visual_slam.git|e31f4cc1d41a329a01946e5fe63669f8b15da677"
)

command -v git >/dev/null || { echo "ERROR: git not found" >&2; exit 1; }
if command -v git-lfs >/dev/null 2>&1; then
  git lfs install --skip-repo
else
  echo "WARNING: git-lfs not installed - run_dev.sh will fail until it is." >&2
fi

for entry in "${REPOS[@]}"; do
  IFS='|' read -r name url sha <<< "$entry"
  dir="$SRC_DIR/$name"

  if [ -d "$dir/.git" ]; then
    if [ "$(git -C "$dir" rev-parse HEAD)" = "$sha" ]; then
      echo "== $name already at $sha"
      continue
    fi
    echo "== $name: fetching, checking out $sha"
    git -C "$dir" fetch origin
  elif [ -e "$dir" ]; then
    echo "ERROR: $dir exists but is not a git repo - move it aside and re-run" >&2
    exit 1
  else
    echo "== $name: cloning"
    git clone --filter=blob:none "$url" "$dir"
  fi
  git -C "$dir" -c advice.detachedHead=false checkout "$sha"
done

dest="$SRC_DIR/isaac_ros_common/scripts/.isaac_ros_common-config"
cp "$SETUP_DIR/.isaac_ros_common-config" "$dest"
echo "== copied config -> $dest"

echo
echo "Done. Start the container with:"
echo "  $SRC_DIR/isaac_ros_common/scripts/run_dev.sh"
