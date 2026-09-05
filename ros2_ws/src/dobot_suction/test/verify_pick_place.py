"""Validate the complete Gazebo pick/place workflow in a sourced ROS environment."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import uuid

from google.protobuf import text_format
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.stringmsg_pb2 import StringMsg
from gz.msgs10.clock_pb2 import Clock


class Processes:
    def __init__(self, env):
        self.env = env
        self.children = []
        self.files = []

    def start(self, command, output, error=None):
        stdout = output.open('w')
        self.files.append(stdout)
        stderr = subprocess.STDOUT
        if error is not None:
            stderr = error.open('w')
            self.files.append(stderr)
        process = subprocess.Popen(command, env=self.env, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        self.children.append(process)
        return process

    @staticmethod
    def stop(process):
        for sig, timeout in ((signal.SIGINT, 4), (signal.SIGTERM, 2),
                             (signal.SIGKILL, 2)):
            try:
                os.killpg(process.pid, sig)
            except ProcessLookupError:
                break
            try:
                process.wait(timeout=timeout)
                # The leader can exit before its children finish closing.
                os.killpg(process.pid, 0)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if process.poll() is not None:
                    break
        process.wait(timeout=2)

    def probe(self, command, timeout):
        process = subprocess.Popen(command, env=self.env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True,
                                   start_new_session=True)
        try:
            output, _ = process.communicate(timeout=timeout)
            return process.returncode, output
        except subprocess.TimeoutExpired:
            self.stop(process)
            output, _ = process.communicate()
            return 124, output
        except BaseException:
            self.stop(process)
            raise

    def close(self):
        for process in reversed(self.children):
            self.stop(process)
        for file in self.files:
            file.close()


def wait_ready(processes, launch, output_dir):
    deadline = time.monotonic() + 60
    clock_found = False
    active = set()
    with (output_dir / 'readiness.log').open('w') as log:
        while time.monotonic() < deadline:
            if launch.poll() is not None:
                raise RuntimeError('Simulation launch exited before controllers became ready')
            checks = [(['ros2', 'control', 'list_controllers'], 'controllers')]
            if not clock_found:
                checks.append((['ros2', 'topic', 'list', '--no-daemon',
                                '--spin-time', '1'], 'topics'))
            for command, label in checks:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                code, output = processes.probe(command, min(5, remaining))
                log.write(f'{label}: exit={code}\n{output}\n')
                log.flush()
                clean = re.sub(r'\x1b\[[0-9;]*m', '', output)
                if label == 'controllers' and code == 0:
                    active = {parts[0] for line in clean.splitlines()
                              if len(parts := line.split()) >= 3 and parts[-1] == 'active'}
                elif label == 'topics' and code == 0:
                    clock_found = '/clock' in clean.splitlines()
            if clock_found and {'arm_controller', 'joint_state_broadcaster'} <= active:
                return sorted(active)
            time.sleep(min(0.5, max(0, deadline - time.monotonic())))
    raise RuntimeError(f'Readiness timeout: active={sorted(active)}, clock={clock_found}')


def read_messages(path, message_type):
    # gz topic -e separates protobuf DebugString messages with an empty line.
    records = path.read_text().split('\n\n') if path.exists() else []
    messages = []
    parse_errors = 0
    for index, record in enumerate(records):
        if not record.strip():
            continue
        try:
            messages.append(text_format.Parse(record, message_type()))
        except text_format.ParseError:
            # SIGINT can interrupt the final write; interior corrupt records fail.
            if index != len(records) - 1:
                parse_errors += 1
    return messages, parse_errors


def sim_seconds(processes):
    code, output = processes.probe(['gz', 'topic', '-t', '/clock', '-e', '-n', '1'], 5)
    if code != 0:
        raise RuntimeError('No Gazebo clock samples received')
    clock = text_format.Parse(output, Clock())
    return clock.sim.sec + clock.sim.nsec * 1e-9


def assess(output_dir, summary, failures, minimum_lift):
    poses, pose_errors = read_messages(output_dir / 'poses.pbtxt', Pose_V)
    states, state_errors = read_messages(output_dir / 'suction-state.pbtxt', StringMsg)
    box_positions = [[pose.position.x, pose.position.y, pose.position.z]
                     for message in poses for pose in message.pose
                     if pose.name == 'pick_box']
    transitions = []
    for message in states:
        if not transitions or message.data != transitions[-1]:
            transitions.append(message.data)
    attached = 'attached' in transitions
    released = attached and 'detached' in transitions[transitions.index('attached') + 1:]
    final_state = transitions[-1] if transitions else None
    summary.update(pose_messages=len(poses), box_samples=len(box_positions),
                   state_messages=len(states), state_transitions=transitions,
                   attached=attached, released=released, final_suction_state=final_state,
                   protobuf_parse_errors=pose_errors + state_errors)
    if pose_errors or state_errors:
        failures.append('Invalid protobuf records in transport monitor output')
    if not attached:
        failures.append('No physical attachment was reported')
    if not released:
        failures.append('No release after attachment was reported')
    if final_state != 'detached':
        failures.append(f'Final suction state is {final_state!r}, expected detached')
    if not box_positions:
        failures.append('No world-space pick_box poses were received')
        return
    if not all(math.isfinite(value) for position in box_positions for value in position):
        failures.append('Box pose contains non-finite coordinates')
        return
    initial, final = box_positions[0], box_positions[-1]
    peak = max(box_positions, key=lambda position: position[2])
    lift = peak[2] - initial[2]
    error = math.hypot(final[0] - 0.08, final[1] - 0.16)
    resting_z_error = abs(final[2] - 0.012)
    final_heights = [position[2] for position in box_positions[-20:]]
    final_height_range = max(final_heights) - min(final_heights)
    summary.update(initial_box_xyz_m=initial, highest_box_xyz_m=peak,
                   final_box_xyz_m=final, lift_m=lift,
                   final_table_xy_error_m=error, expected_resting_box_z_m=0.012,
                   final_resting_z_error_m=resting_z_error,
                   final_height_samples=len(final_heights),
                   final_height_range_m=final_height_range)
    if lift < minimum_lift:
        failures.append(f'Box lift {lift:.6f} m is below {minimum_lift:.6f} m')
    if error > 0.04:
        failures.append(f'Final box XY error {error:.6f} m exceeds 0.040000 m')
    if resting_z_error > 0.003:
        failures.append(f'Final box height {final[2]:.6f} m is not near table rest height 0.012 m')
    if len(final_heights) < 20 or final_height_range > 0.001:
        failures.append('Box height must be stable within 0.001 m over the final 20 samples')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('/tmp/dobot-pick-place-check'))
    parser.add_argument('--minimum-lift', type=float, default=0.02)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault('GZ_PARTITION', f'dobot-pick-place-{uuid.uuid4().hex[:12]}')
    env.setdefault('ROS_DOMAIN_ID', '89')
    env.pop('FASTRTPS_DEFAULT_PROFILES_FILE', None)
    env.pop('FASTDDS_DEFAULT_PROFILES_FILE', None)
    processes = Processes(env)
    failures = []
    summary = {'gz_partition': env['GZ_PARTITION'], 'ros_domain_id': env['ROS_DOMAIN_ID'],
               'minimum_lift_m': args.minimum_lift, 'target_table_xy_m': [0.08, 0.16],
               'maximum_table_xy_error_m': 0.04}
    started = time.monotonic()

    def interrupted(signum, _frame):
        raise RuntimeError(f'Validation interrupted by signal {signum}')

    signal.signal(signal.SIGTERM, interrupted)
    try:
        launch = processes.start(
            ['ros2', 'launch', 'dobot_magician_ros', 'simulation.launch.py', 'gui:=false'],
            args.output_dir / 'launch.log')
        for topic, filename in (('/world/suction_turn/pose/info', 'poses'),
                                ('/dobot_magician/suction_state', 'suction-state')):
            processes.start(['gz', 'topic', '-t', topic, '-e'],
                            args.output_dir / f'{filename}.pbtxt',
                            args.output_dir / f'{filename}-stderr.log')
        summary['active_controllers'] = wait_ready(processes, launch, args.output_dir)
        processes.start(['ros2', 'topic', 'echo', '/arm_controller/controller_state',
                         'control_msgs/msg/JointTrajectoryControllerState'],
                        args.output_dir / 'controller-state.yaml')
        sim_start = sim_seconds(processes)
        motion_deadline = time.monotonic() + 120
        player = processes.start(['ros2', 'run', 'dobot_magician_ros', 'trajectory_player'],
                                 args.output_dir / 'trajectory-player.log')
        try:
            summary['trajectory_player_exit_code'] = player.wait(timeout=100)
            if player.returncode != 0:
                failures.append(f'Trajectory player exited with code {player.returncode}')
        except subprocess.TimeoutExpired:
            processes.stop(player)
            failures.append('Trajectory player exceeded its 100 second wall timeout')
        # A wall-time player can exit before an 8-second simulated trajectory ends.
        sim_end = sim_seconds(processes)
        while sim_end - sim_start < 12 and time.monotonic() < motion_deadline:
            time.sleep(1)
            sim_end = sim_seconds(processes)
        summary['observed_motion_sim_seconds'] = sim_end - sim_start
        if sim_end - sim_start < 12:
            failures.append('Simulation did not advance through the complete trajectory')
        if launch.poll() is not None:
            failures.append('Simulation launch exited during the trajectory')
    except (Exception, KeyboardInterrupt) as error:
        failures.append(f'{type(error).__name__}: {error}')
    finally:
        processes.close()
    try:
        assess(args.output_dir, summary, failures, args.minimum_lift)
    except Exception as error:
        failures.append(f'Monitor analysis failed: {type(error).__name__}: {error}')
    summary.update(result='FAIL' if failures else 'PASS', failures=failures,
                   elapsed_wall_seconds=time.monotonic() - started)
    rendered = json.dumps(summary, indent=2, allow_nan=False)
    (args.output_dir / 'summary.json').write_text(rendered + '\n')
    print(rendered, flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
