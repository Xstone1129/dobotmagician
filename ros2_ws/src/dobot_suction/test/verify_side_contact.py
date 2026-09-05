"""Start an isolated world and verify actual side contact cannot attach."""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET


env = dict(os.environ, GZ_PARTITION=f'dobot_side_contact_{os.getpid()}')
tree = ET.parse(Path(__file__).with_name('contact.sdf'))
box = tree.find(".//model[@name='pick_box']")
box.find('pose').text = '0.029 0 0.16 0 0 0'
box.find('.//box/size').text = '0.02 0.02 0.30'
sensor = tree.find(".//sensor[@name='suction_contact']")
ET.SubElement(sensor.find('contact'), 'topic').text = '/test/side_contacts'

with tempfile.TemporaryDirectory(prefix='dobot-side-') as directory:
    world = Path(directory) / 'side.sdf'
    tree.write(world)
    with (Path(directory) / 'server.log').open('w+') as log:
        server = subprocess.Popen(['gz', 'sim', '-s', str(world)], env=env,
                                  stdout=log, stderr=log, start_new_session=True)
        monitor = None
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                topics = subprocess.check_output(['gz', 'topic', '-l'], env=env,
                                                 text=True, timeout=5)
                if '/dobot_magician/suction/enable' in topics:
                    break
                time.sleep(0.2)
            else:
                raise AssertionError('Suction plugin did not start')
            monitor = subprocess.Popen(
                ['gz', 'topic', '-e', '-t', '/test/side_contacts', '-n', '30'],
                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run(['gz', 'topic', '-t', '/dobot_magician/suction/enable',
                            '-m', 'gz.msgs.Boolean', '-p', 'data: true'],
                           env=env, check=True, timeout=5)
            time.sleep(0.5)
            subprocess.run(['gz', 'service', '-s', '/world/contact_test/control',
                            '--reqtype', 'gz.msgs.WorldControl', '--reptype',
                            'gz.msgs.Boolean', '--timeout', '3000',
                            '--req', 'pause: false'], env=env, check=True, timeout=5,
                           capture_output=True)
            contacts, errors = monitor.communicate(timeout=10)
            assert 'collision1 {' in contacts, f'No physical side contact observed: {errors}'
            states = subprocess.check_output(
                ['gz', 'topic', '-e', '-t', '/dobot_magician/suction_state', '-n', '10'],
                env=env, timeout=5, text=True)
            assert 'data: "attached"' not in states, states
            assert 'data: "detached"' in states, states
            log.flush()
            log.seek(0)
            assert 'bottom contact, attached' not in log.read()
            print('PASS: physical contact on the cup side with suction enabled did not attach')
        finally:
            if monitor is not None and monitor.poll() is None:
                monitor.kill()
                monitor.communicate()
            os.killpg(server.pid, signal.SIGINT)
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGKILL)
                server.wait()
