# -----------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -----------------------------------------------------------------------------

"""
This module tests the CodeChecker command line.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import os
import subprocess
import unittest

from libtest import env


def run_cmd(cmd, env=None):
    print(cmd)
    proc = subprocess.Popen(cmd,
                            env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = proc.communicate()
    print(out)
    return proc.returncode, out, err


class TestCmdline(unittest.TestCase):
    """
    Simple tests to check CodeChecker command line.
    """

    def setUp(self):

        test_workspace = os.environ.get('TEST_WORKSPACE')

        test_class = self.__class__.__name__
        print('Running ' + test_class + ' tests in ' + test_workspace)

        codechecker_cfg = env.import_test_cfg(test_workspace)[
            'codechecker_cfg']
        self.server_url = env.parts_to_url(codechecker_cfg)

        # Get the test project configuration from the prepared test workspace.
        self._testproject_data = env.setup_test_proj_cfg(test_workspace)
        self.assertIsNotNone(self._testproject_data)

        # Setup a viewer client to test viewer API calls.
        self._cc_client = env.setup_viewer_client(test_workspace)
        self.assertIsNotNone(self._cc_client)

        # Get the CodeChecker cmd if needed for the tests.
        self._codechecker_cmd = env.codechecker_cmd()

        self._test_config = env.import_test_cfg(test_workspace)

    def test_main_help(self):
        """ Main cmdline help. """

        main_help = [env.codechecker_cmd(), '--help']
        self.assertEqual(0, run_cmd(main_help)[0])

    def test_version_help(self):
        """ Test the 'version' subcommand. """

        version_help = [env.codechecker_cmd(), 'version', '--help']
        self.assertEqual(0, run_cmd(version_help)[0])

    def test_check_help(self):
        """ Get help for check subcmd. """

        check_help = [env.codechecker_cmd(), 'check', '--help']
        self.assertEqual(0, run_cmd(check_help)[0])

    def test_server_help(self):
        """ Get help for server subcmd. """

        srv_help = [env.codechecker_cmd(), 'server', '--help']
        self.assertEqual(0, run_cmd(srv_help)[0])

    def test_checkers(self):
        """ Listing available checkers. """

        checkers_cmd = [env.codechecker_cmd(), 'checkers']
        self.assertEqual(0, run_cmd(checkers_cmd)[0])

    def test_sum(self):
        """ Test cmd sum command. """

        sum_res = [self._codechecker_cmd, 'cmd', 'sum',
                   '-a', '--url', str(self.server_url)]

        ret = run_cmd(sum_res,
                      env=self._test_config['codechecker_cfg']['check_env'])[0]
        self.assertEqual(0, ret)

    def test_runs_filter(self):
        """ Test cmd results filter command. """

        env = self._test_config['codechecker_cfg']['check_env']

        # Get runs without filter.
        res_cmd = [self._codechecker_cmd, 'cmd', 'runs',
                   '-o', 'json', '--url', str(self.server_url)]
        ret, res, _ = run_cmd(res_cmd, env=env)

        self.assertEqual(0, ret)
        self.assertEqual(2, len(json.loads(res)))

        # Filter both runs.
        res_cmd = [self._codechecker_cmd, 'cmd', 'runs',
                   '-o', 'json', '-n', 'test_files*',
                   '--url', str(self.server_url)]
        ret, res, _ = run_cmd(res_cmd, env=env)

        self.assertEqual(0, ret)
        self.assertEqual(2, len(json.loads(res)))

        # Filter only one run.
        res_cmd = [self._codechecker_cmd, 'cmd', 'runs',
                   '-o', 'json', '-n', 'test_files1*',
                   '--url', str(self.server_url)]
        ret, res, _ = run_cmd(res_cmd, env=env)

        self.assertEqual(0, ret)
        self.assertEqual(1, len(json.loads(res)))

    def test_results_multiple_runs(self):
        """
        Test cmd results with multiple run names.
        """
        check_env = self._test_config['codechecker_cfg']['check_env']

        res_cmd = [self._codechecker_cmd, 'cmd', 'results', 'test_files1*',
                   'test_files1*', '-o', 'json', '--url', str(self.server_url)]

        ret, res, _ = run_cmd(res_cmd, env=check_env)
        self.assertEqual(0, ret)

    def test_stderr_results(self):
        """
        Test results command that we redirect logger's output to the stderr if
        the given output format is not table.
        """
        check_env = self._test_config['codechecker_cfg']['check_env']

        res_cmd = [self._codechecker_cmd, 'cmd', 'results', 'non_existing_run',
                   '-o', 'json', '--url', str(self.server_url)]

        ret, res, err = run_cmd(res_cmd, env=check_env)
        self.assertEqual(1, ret)
        self.assertEqual(res, '')
        self.assertIn('No runs were found!', err)

    def test_stderr_sum(self):
        """
        Test sum command that we redirect logger's output to the stderr if
        the given output format is not table.
        """
        check_env = self._test_config['codechecker_cfg']['check_env']

        res_cmd = [self._codechecker_cmd, 'cmd', 'sum', '-n',
                   'non_existing_run', '-o', 'json', '--url',
                   str(self.server_url)]

        ret, res, err = run_cmd(res_cmd, env=check_env)
        self.assertEqual(1, ret)
        self.assertEqual(res, '')
        self.assertIn('No runs were found!', err)
