FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy \
    PYTHONUNBUFFERED=1 \
    RMW_IMPLEMENTATION=rmw_fastrtps_cpp

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-venv python3-numpy python3-scipy python3-sklearn \
    python3-matplotlib python3-yaml python3-joblib \
    ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-gz-ros2-control \
    ros-jazzy-controller-manager ros-jazzy-joint-state-publisher-gui \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/dobotmagician
COPY . .

RUN python3 -m pip install --no-cache-dir --break-system-packages -e . \
    && . /opt/ros/jazzy/setup.sh \
    && colcon build --symlink-install --base-paths ros2_ws/src

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
