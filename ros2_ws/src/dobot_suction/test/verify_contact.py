"""Run against contact.sdf in the same GZ_PARTITION; requires gz-msgs Python path."""
import json
import subprocess
import time

from google.protobuf import text_format
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.stringmsg_pb2 import StringMsg


def publish(topic, msg_type, payload):
    subprocess.run(['gz', 'topic', '-t', topic, '-m', msg_type, '-p', payload],
                   check=True, timeout=5, capture_output=True)


def read(topic, message):
    output = subprocess.run(['gz', 'topic', '-t', topic, '-e', '-n', '1'],
                            check=True, timeout=5, capture_output=True, text=True)
    return text_format.Parse(output.stdout, message)


def state():
    return read('/dobot_magician/suction_state', StringMsg()).data


def height():
    poses = read('/world/contact_test/pose/info', Pose_V())
    return next(p.position.z for p in poses.pose if p.name == 'pick_box')


def wait_for(predicate):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise AssertionError('Timed out waiting for physical test condition')


assert state() == 'detached', 'Must not attach before contact'
initial = height()
publish('/test/lift', 'gz.msgs.Double', 'data: -0.13')
time.sleep(3)
assert state() == 'detached', 'Suction must start disabled even in contact'
publish('/test/lift', 'gz.msgs.Double', 'data: 0')
time.sleep(3)
assert height() < 0.03, 'Disabled suction must not lift the box'
publish('/dobot_magician/suction/enable', 'gz.msgs.Boolean', 'data: true')
time.sleep(1)
assert state() == 'detached', 'Enabled suction must not attach at a distance'
publish('/test/lift', 'gz.msgs.Double', 'data: -0.13')
wait_for(lambda: state() == 'attached')
publish('/test/lift', 'gz.msgs.Double', 'data: 0')
wait_for(lambda: height() > 0.1)
lifted = height()
publish('/dobot_magician/suction/enable', 'gz.msgs.Boolean', 'data: false')
wait_for(lambda: state() == 'detached')
wait_for(lambda: height() < 0.03)
released = height()
publish('/test/lift', 'gz.msgs.Double', 'data: -0.13')
time.sleep(3)
assert state() == 'detached', 'Release must inhibit automatic reattachment'
publish('/dobot_magician/attach', 'gz.msgs.Empty', 'unused: true')
wait_for(lambda: state() == 'attached')
publish('/dobot_magician/detach', 'gz.msgs.Empty', 'unused: true')
wait_for(lambda: state() == 'detached')
print(json.dumps({'initial_box_z': initial, 'lifted_box_z': lifted,
                  'released_box_z': released, 'contact_lift_release_reattach': 'PASS'}))
