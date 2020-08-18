import os
import logging
import pathlib
import tempfile
import simplejson
from requests import Response

import hutch_python.bug
from hutch_python.bug import (get_current_environment, report_bug,
                              get_text_from_editor)

logger = logging.getLogger(__name__)


# Mock user input function that just returns the prompt
def user_input(prompt):
    return prompt


# Mock requests.Session to avoid actual GitHub posts
class FakeSession:
    handle = None
    past_auth = dict()
    proxies = dict()

    def __init__(self):
        pass

    @property
    def auth(self):
        return self.past_auth

    @auth.setter
    def auth(self, auth_info):
        logger.debug('Updating authorization %s', auth_info)
        self.past_auth.update(dict([auth_info]))

    def post(self, url, json_dump):
        # Dump the JSON to handle
        if self.handle:
            logger.debug('Dumping JSON to %s', self.handle.name)
            self.handle.write(json_dump)
        # Create a fake response
        r = Response()
        r.status_code = 201
        return r


def test_get_current_environment():
    logger.debug('test_get_current_environment')
    # Development packages
    fk_pkgs = ['one', 'two', 'three']
    os.environ['CONDA_ENVNAME'] = 'test-environment'
    with tempfile.TemporaryDirectory() as tmp:
        logger.debug('Creating temp directory %s', tmp)
        # Set a PythonPath
        os.environ['PYTHONPATH'] = tmp
        # Create fake packages
        for pkg in fk_pkgs:
            pathlib.Path(os.path.join(tmp, pkg)).touch()
        env, pkgs = get_current_environment()
        assert all([pkg in pkgs for pkg in fk_pkgs])
        assert env == 'test-environment'


def test_bug_report(monkeypatch, temporary_config):
    logger.debug('test_bug_report')
    # Patch in our fake user input function
    monkeypatch.setattr(hutch_python.bug, 'request_input', user_input)
    # Patch in fake requests.Session
    monkeypatch.setattr(hutch_python.bug.requests, 'Session', FakeSession)
    # Create a fake issue and requests.Session
    with tempfile.NamedTemporaryFile('w+', delete=False) as tmp:
        # Write to our fake file instead of GitHub
        FakeSession.handle = tmp
        # Post report
        report_bug(captured_output='A printed message',
                   description='A description of the bug')
    bug = simplejson.load(open(tmp.name, 'r'))
    # Check GitHub authentication
    assert FakeSession.past_auth == {'github_user': 'github_pw'}
    # Test proxy host information
    assert FakeSession.proxies == {'https': 'http://proxyhost:11111'}
    # See that we catch the fake environment
    assert bug['title'].startswith('Please')


def test_get_text_from_editor(monkeypatch):
    logger.debug("test_get_text_from_editor")

    # Mock write function
    def write_text(info):
        open(info[1], 'w+').write(info[0])

    # Patch in our fake write_text
    monkeypatch.setattr(hutch_python.bug.subprocess, 'call', write_text)
    os.environ['EDITOR'] = 'vim'
    assert get_text_from_editor() == 'vim'
