import os
import pathlib
import tempfile
import unittest

from fabrictestbed.util.constants import Constants

from fabrictestbed_extensions.fablib.fablib import FablibManager


class FablibManagerTests(unittest.TestCase):
    """
    Some basic tests to exercise FablibManager.

    Instantiating FablibManager will throw some exceptions if some
    required environment variables are not set.
    """

    required_env_vars = [
        Constants.FABRIC_CREDMGR_HOST,
        Constants.FABRIC_ORCHESTRATOR_HOST,
        Constants.FABRIC_PROJECT_ID,
        # Constants.FABRIC_TOKEN_LOCATION,
        FablibManager.FABRIC_BASTION_HOST,
        FablibManager.FABRIC_BASTION_USERNAME,
        FablibManager.FABRIC_BASTION_KEY_LOCATION,
    ]

    def setUp(self):
        # Run each test with an empty environment.
        os.environ.clear()

        # Create an empty configuration file, so that we will be
        # really testing with a clean slate.  Creating the
        # configuration file in read-only mode should ensure that it
        # will remain empty.
        self.rcfile = tempfile.NamedTemporaryFile(mode="r")
        self.rcfile.flush()

    def tearDown(self):
        self.rcfile.close()

    def test_fablib_manager_no_env_vars(self):
        # Test with no required env vars set.
        self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_one_env_var(self):
        # Test with some required env vars set.
        for var in self.required_env_vars:
            os.environ[var] = "dummy"
            self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_all_env_vars(self):
        # Test with all required configuration except
        # FABRIC_TOKEN_LOCATION.
        for var in self.required_env_vars:
            os.environ[var] = "dummy"

        self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_test_only_cm_host(self):
        os.environ[Constants.FABRIC_CREDMGR_HOST] = "dummy"
        self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_test_only_orchestrator_host(self):
        os.environ[Constants.FABRIC_ORCHESTRATOR_HOST] = "dummy"
        self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_test_only_project_id(self):
        os.environ[Constants.FABRIC_PROJECT_ID] = "dummy"
        self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_test_only_token_location(self):
        os.environ[Constants.FABRIC_TOKEN_LOCATION] = "dummy"
        self.assertRaises(AttributeError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_test_with_no_token_file(self):
        # Should fail when token location is not a valid path.

        # set all required env vars.
        for var in self.required_env_vars:
            os.environ[var] = "dummy"

        os.environ[Constants.FABRIC_TOKEN_LOCATION] = "dummy"

        # FablibManager() without a valid token or token location
        # should raise a "ValueError: Invalid value for
        # `refresh_token`, must not be `None`"
        try:
            FablibManager(fabric_rc=self.rcfile.name)
            print("Success")
        except Exception as e:
            print(f"KOMAL--- exception: {e}")
        #self.assertRaises(ValueError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_test_with_dummy_token(self):
        # TODO: That FablibManager() calls build_slice_manager()
        # complicates writing a test for it.  It eventually makes a
        # network call to credential manager API, but it is not right
        # for a unit test to do such a thing.  We could probably
        # somehow mock a CM here?

        # set all required env vars.
        for var in self.required_env_vars:
            os.environ[var] = "dummy"

        # '.invalid' is an invalid host per RFC 6761, so this test
        # must fail without ever making a successful network call.
        os.environ[Constants.FABRIC_CREDMGR_HOST] = ".invalid"
        path = pathlib.Path(__file__).parent / "data" / "dummy-token.json"
        os.environ[Constants.FABRIC_TOKEN_LOCATION] = f"{path}"

        self.assertRaises(ValueError, FablibManager, fabric_rc=self.rcfile.name)

    def test_fablib_manager_with_empty_config(self):
        # Check that an empty configuration file will cause
        # FablibManager to raise an error.
        rcfile = tempfile.NamedTemporaryFile()
        rcfile.flush()

        with self.assertRaises(AttributeError):
            FablibManager(fabric_rc=rcfile.name)

    def test_fablib_manager_with_some_config(self):
        # Test with some configuration in the rc file.
        rcfile = tempfile.NamedTemporaryFile()

        # Write all configuration except FABRIC_TOKEN_LOCATION.  The
        # token location is a special case because when it is set,
        # Fablib will need network access to reach CredentialManager.
        for var in self.required_env_vars:
            rcfile.write(f"export {var} = dummy\n".encode())

        rcfile.flush()

        with self.assertRaises(AttributeError) as ctx:
            FablibManager(fabric_rc=rcfile.name)

        # Check that the error is what we expected.
        self.assertIsInstance(ctx.exception, AttributeError)

        # Check that the error message is what we expected: the only
        # error should be about missing token.
        self.assertEqual(
            str(ctx.exception),
            "Error initializing FablibManager: ['FABRIC token is not set']",
        )
