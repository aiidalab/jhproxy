from dockerspawner import DockerSpawner
from jupyterhub.handlers.base import BaseHandler
from tornado.escape import xhtml_escape
from tornado import gen
from tornado import httpclient, httputil
from tornado.web import authenticated
from jhproxy.spawners import TokenizedDockerSpawner
import json


class ProxyBaseHandler(BaseHandler):
    """
    Base class for the handler, do not use directly.
    """
    def _set_proxy_custom_headers(self):
        # Allow CORS requests
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "X-Proxy-Token")

    def set_default_headers(self):
        super().set_default_headers()
        self._set_proxy_custom_headers()

    def options(self, username, proxy_path): # pylint: disable=arguments-differ,unused-argument
        """Activate OPTIONS HTTP request, needed for CORS requests from AJAX"""
        # no body
        self.set_status(204)
        self.finish()

    # Get the global port
    proxy_port = None

    def initialize(self, proxy_port=None): # pylint: disable=arguments-differ
        """
        Set the value of the port (inside the docker container) 
        that we want to proxy out.
        """
        self.proxy_port = proxy_port

    @gen.coroutine
    def get_proxied_port(self, spawner):
        """
        Return the port on the host that maps to the proxy_port in the docker
        container.
        """
        ## Get the port
        inspection = yield spawner.docker("inspect_container",
                                          spawner.container_id)
        port_mappings = inspection.get('NetworkSettings', {}).get('Ports', {})

        self.log.debug("Port mappings:{}".format(str(port_mappings)))

        port_routes = port_mappings.get('{}/tcp'.format(self.proxy_port), [])
        host_port = None
        for port_route in port_routes:
            if port_route.get('HostIp', '') == spawner.host_ip:
                host_port = port_route.get('HostPort', '')
                try:
                    host_port = int(host_port)
                except ValueError:
                    host_port = None
                break
        raise gen.Return(host_port)

    def get_spawner_from_username(self, username):
        """
        Given a username, return the corresponding (docker) spawner.

        Return None if not found.
        """
        user = self.user_from_username(username)
        self.log.debug("User: {}".format(str(user)))
        spawners = user.spawners.values()
        spawner = None
        # Get the first DockerSpawner
        for _spawner in spawners:
            if isinstance(_spawner, DockerSpawner):
                spawner = _spawner
                break
        return spawner


class ProxyTokenHandler(ProxyBaseHandler):
    """
    Manage the token (release, creation, ...) for the proxy.
    All requests need to be authenticated (user need to be logged into 
    jupyterhub in the same browser).

    * GET request: return the current token
    * POST request: change the token
    """

    @authenticated
    def get(self): # pylint: disable=arguments-differ
        """
        Get the current token.

        Return a JSON value with the token (typically `null`, or a string)
        """
        spawner = self.get_spawner_from_username(self.current_user.name)
        #self.write(xhtml_escape(str(spawner)))
        #self.write("<br>")
        if spawner is None:
            self.set_status(503)
            self.write("Spawner not available")
            return

        try:
            proxy_token = spawner.proxy_token
        except AttributeError:
            ## E.g. if we are using a standard DockerSpawner
            ## Then the proxy_token is set to an empty string
            proxy_token = ""
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(proxy_token))

    @authenticated
    def post(self): # pylint: disable=arguments-differ
        """
        Ask to change the token.
        
        Body: needs to be a string with one of the following values:
          * "disabled": sets the Token to `null` (or `None` in python),
            effectively disabling the proxy
          * "allow_all": sets the Token to `""`, effectively allowing the proxy 
            with no authorization check
          * "random": regenerate a random token

        If the body in the POST request is not a valid value, a 400 code is returned.
        Otherwise, return a JSON value with the new token (typically `null`, or a string)
        """
        spawner = self.get_spawner_from_username(self.current_user.name)
        #self.write(xhtml_escape(str(spawner)))
        #self.write("<br>")
        if spawner is None:
            self.set_status(503)
            self.write("Spawner not available")
            return

        if not isinstance(spawner, TokenizedDockerSpawner):
            self.set_status(500)
            self.write("The spawner is not a TokenizedDockerSpawner, so it "
                       "does not hold a token state. If you use a standard "
                       "DockerSpawner, do not activate this RequestHandler")
            return

        body = self.request.body
        if not body:
            body = b''
        if body == b"disabled":
            spawner.set_token(None)
        elif body == b"allow_all":
            spawner.set_token("")
        elif body == b"random":
            spawner.regenerate_random_token()
        else:
            self.set_status(400)
            self.write(
                "Invalid action required in the POST body for the proxy-token endpoint: {}"
                .format(body))
            return

        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(spawner.proxy_token))


class ProxyHandler(ProxyBaseHandler):
    """
    This class is a RequestHandler to proxy requests.

    When defining the routes, use something like the following:

    ```
    (r'/proxy/([^/]+)(/.*)', ProxyHandler, dict(proxy_port=5000))
    ```

    that is, two parts in the URL regex, one to match the username, and one to 
    match the rest of the URL. Moreover, pass the proxy_port (inside the docke container) that you want to proxy.

    If you just use a standard DockerSpawner, all requests will be proxied
    without an authorization check.
    If instead you use a `jbproxy.spawners.TokenizedDockerSpanwer`, the
    token persisted by it will be used for authorization (note that this
    is stored in the spawner, so it is shared between all proxies acting 
    on the same docker machine/spawner).

    Behavior for the token:
    - If the token set in the spawner is `None`: access disabled, all requests
      will not be authorized and return a 403 HTTP error.
    - If the token set in the spawner is `""`: access enabled without 
      authorization checks, all requests are proxied.
    - If the token set in the spawner is a non-empty string: access enabled; 
      the HTTP headers are checked to see if there is a `X-Proxy-Token`
      with the same value as the one stored in the spawner.
      If this is the case: the request is proxied, otherwise a 403 HTTP error
      is returned.
    
    Other possible behaviors/error codes:
    - If the user specified in the URL is not found: a 404 error is returned
    - If the docker container is not configured to forward the `proxy_port` 
      inside the docker container: a 503 error is returned
    - Other error statuses (including the fact that there is no service 
      listening behind the port, inside the docker container) typically result
      in a 500 error.
    """

    @gen.coroutine
    def get(self, username, proxy_path=''): # pylint: disable=arguments-differ
        '''Manage proxy redirection, optionally with authorization (depending
        on the spawner).'''

        if self.proxy_port is None:
            self.set_status(500)
            self.write(
                "Proxy port not configured, pass it as an option when defining " "the handlers routes<br>"
                "E.g. (r'/proxy/([^/]+)(/.*)', ProxyHandler, dict(proxy_port=proxy_port))"
            )
            return

        self.log.debug('Username: {}; Port: {}; Proxy path: {}'.format(
            username, self.proxy_port, proxy_path))

        spawner = self.get_spawner_from_username(username)
        if spawner is None:
            self.log.debug(
                "No DockerSpawner found (only DockerSpawner supported)")
            self.set_status(404)
            self.write("Not found or not available")
            return

        ## Get the port
        host_port = yield self.get_proxied_port(spawner)

        if host_port is None:
            self.set_status(503)
            self.write("Not port mapping enabled in the docker container")
            return
        self.log.debug("Host port:{}".format(str(host_port)))

        if isinstance(spawner, TokenizedDockerSpawner):
            expected_token = spawner.proxy_token
        else:
            # If this is not a TokenizedDockerSpawner: then we always
            # allow the request
            expected_token = ""

        # We pop the header, to avoid to expose it to the service inside
        # the docker container
        proxy_token = self.request.headers.pop('X-Proxy-Token', "")
        # Both a token header of "", a missing header, and a value `null`
        # are converted to an empty string, and they all mean you
        # do not want to pass a token.
        if proxy_token is None:
            proxy_token = ""
        if expected_token is None:
            self.set_status(403)
            self.write("Unauthorized access (disabled)")
            return

        # Actual authentication check
        # If the expected_token is "", it means 'allow all' and
        # therefore the check is skipped completely, even
        # if a different token is passed
        if expected_token != "":
            if proxy_token != expected_token:
                self.set_status(403)
                self.write("Unauthorized access")
                return

        # Ok, we are authenticated: proxy the request
        yield self.proxy( # pylint: disable=not-callable
            uri='http://{}'.format(spawner.host_ip),
            port=host_port,
            proxied_path=proxy_path)

    @gen.coroutine
    def proxy(self,uri, port, proxied_path): # pylint: disable=arguments-differ
        """
        Proxy the request.
        """
        if 'Proxy-Connection' in self.request.headers:
            del self.request.headers['Proxy-Connection']

        if self.request.headers.get("Upgrade", "").lower() == 'websocket':
            self.set_status(500)
            self.write("Not enabled for websocket")
            return

        body = self.request.body
        if not body:
            if self.request.method == 'POST':
                body = b''
            else:
                body = None

        client_uri = '{uri}:{port}{path}'.format(
            uri=uri, port=port, path=proxied_path)
        if self.request.query:
            client_uri += '?' + self.request.query

        client = httpclient.AsyncHTTPClient()

        self.log.debug("client_uri: {}".format(client_uri))

        req = httpclient.HTTPRequest(
            client_uri,
            method=self.request.method,
            body=body,
            headers=self.request.headers,
            follow_redirects=False)

        response = yield client.fetch(req, raise_error=False)

        # Return a 500 error for all non-HTTP errors
        if response.error and type(response.error) is not httpclient.HTTPError:
            self.set_status(500)
            self.write("{}".format(xhtml_escape(str(response.error))))
        else:
            self.set_status(response.code, response.reason)

            # clear tornado default headers
            self._headers = httputil.HTTPHeaders()

            # Set the CORS headers
            self._set_proxy_custom_headers()

            # reset the headers
            for header, v in response.headers.get_all():
                if header not in ('Content-Length', 'Transfer-Encoding',
                                  'Content-Encoding', 'Connection'):
                    # some header appear multiple times, eg 'Set-Cookie'
                    self.add_header(header, v)

            if response.body:
                self.write(response.body)
