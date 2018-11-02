from traitlets import Unicode
import dockerspawner
import random
import string


class TokenizedDockerSpawner(dockerspawner.DockerSpawner):

    default_startup_behavior = Unicode(
        "disabled",
        config=True,
        help="""The default behavior for the token.

        This flag decides how to set the default behavior
        the first time the spawner is generated, when it is not set.
        Note that once generated, a restart of jupyterhub will not 
        change the token (unless something is set in the shutdown_behavior),
        to this behavior occurs only one (it will occur again if you delete
        the jupyterhub database or remove the spawner entry from there).

        Allowed values:
        * 'disabled': set to `None` at startup (in `jhproxy`
          this means that proxy is effectively disabled).
        * 'allow_all': set to `''` (empty string) at startup (in `jhproxy`
          this means that proxy is enabled without any authorization token
          required).
        * 'random': if no token is present, generate a random token 
          (this enabled the proxy by default in a secure mode).
        """,
    )

    shutdown_behavior = Unicode(
        "pass",
        config=True,
        help="""The behavior for the token on shutdown of the spawner.

        This flag decides what to do at shutdown.
        Note that if you set "disable", a restart of jupyterhub will
        leave it disabled - so use with care.

        Allowed values:
        * "pass": do nothing. At the next startup, the same token will be
          reused (possibly remaining in a 'disabled' or 'allow_all') state.
        * "disable": disable at shutdown. At the next startup the token will
          still be disabled, if the spawner is persisted. If the spawner is 
          instead deleted, a new token will be generated depending on the
          value of `TokenizedDockerSpahwer.default_startup_behavior`.
        """)

    @property
    def proxy_token(self):
        """
        Return the current token.
        """
        return self._proxy_token

    def regenerate_random_token(self, length=40):
        """Replace the token with a new, randomly generated one"""
        self._proxy_token = ''.join(
            random.choice(string.ascii_lowercase + string.digits)
            for _ in range(length))

    def set_token(self, new_token):
        """Set a token as chosen by the user"""
        self._proxy_token = new_token

    def get_state(self):
        """
        Get the current state; store the proxy token in the DB.

        It is stored at shutdown
        """
        state = super().get_state()
        state['proxy_token'] = self._proxy_token
        return state

    def load_state(self, state):
        """
        Load state from the database, including the proxy token from the DB
        """
        super().load_state(state)
        if 'proxy_token' in state:
            self._proxy_token = state['proxy_token']
        else:
            if self.default_startup_behavior == "disabled":
                self._proxy_token = None
            elif self.default_startup_behavior == "allow_all":
                self._proxy_token = ""
            elif self.default_startup_behavior == "random":
                self.regenerate_random_token()
            else:
                raise RuntimeError(
                    "The 'default_startup_behavior' was set to an unknown value '{}"
                    .format(self.default_startup_behavior))

    def clear_state(self):
        """
        Clear any state (called after shutdown)
        """
        super().clear_state()
        if self.shutdown_behavior == "pass": # pylint: disable=no-else-return
            return
        elif self.shutdown_behavior == "disable":
            self._proxy_token = None
        else:
            raise RuntimeError(
                "The 'shutdown_behavior' was set to an unknown value '{}".
                format(self.shutdown_behavior))
