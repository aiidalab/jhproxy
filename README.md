# jhproxy

A port proxy for JupyterHub when using the DockerSpawner, optionally with 
authentication.

This code is hosted at https://github.com/aiidalab/jhproxy.

If you use JupyterHub, and some app inside the docker spawned by Jupyter 
opens a port (e.g. it exposes a REST API), these are not accessible outside the
docker container, in general.

A nice Jupyter server exension, [nbserverproxy](https://github.com/jupyterhub/nbserverproxy), exists to proxy a given port
through the notebook server.
This would work, but requires that anybody performing a request has access to 
the JupyterHub token. This could be extracted from the browser and passed to an
external app that wants to use the API (command line, or throgh AJAX requests
from a different site), but:
- this is cumbersome
- if someone gets the token, they get access to the whole docker container of the
  user

To alleviate this, we wrote `jhproxy`.
This needs to be installed by the person maintaining the JupyterHub installation,
but allows to:
- decide which ports can be forwarded (more can be forwarded, but they need to 
  be specified, see documentation below)
- allow for (optional) authentication of the proxy requests (via a 
  `X-Proxy-Token` that should be passed in the HTTP Request Headers) 
- Allow a logged-in JupyterHub user to enable, disable or regenerate a token
- Add an API endpoint to obtain the current token for the currently logged-in
  JupyterHub user (so this can be given to a client performing the API requests
  via the proxy).

Note that this proxy only works currently for a DockerSpawner (to use 
token authentication you need to use the provided `jhproxy.spawners.TokenizedDockerSpawner`, that extends the image).

## Documentation

In order to install and use this extension, you need to do the following on
the machine where JupyterHub is installed:

- install `jhproxy`: 
  ```
  pip instal jhproxy
  ```

- configure properly your `jupyterhub_config.py` to decide which ports to 
  proxy, under which address, etc.
  We provide a fully documented working example inside `examples/jupyterhub_config.py`. Feel free to copy, reuse and edit to your needs.

We provide below just a few additional notes on how to configure it

### Authorization setup
If you don't need authorization, you can just use the standard `DockerSpawner` spawner; ports will simply be proxied.

If you instead want authorization, use `jbproxy.spawners.TokenizedDockerSpawner`
as in the configuration example. As shown there, there are also a few options
to decide the default token to be generated the first time the spawner is
create (disabled, allow all, generate new random token).

# How to use it

The user (once logged in JupyterHub) can use the `ProxyTokenHandler` (under the
url `http(s)://JUPYTERHUBHOST/hub/proxytoken/`) to get the current token (via GET requests) or to ask to change it (via POST requests).
This endpoint requires to be authenticated.

To see an example, load inside your jupyter the notebook provided under `examples/Proxy token manager.ipynb`.
Run it and then press the buttons to get the current token, or change it (disabling all access, enabling it for everybody, or generating a new random token).

**NOTE**: this needs to be done inside the jupyter provided by JupyterHub,
otherwise the JupyterHub authorization cookies will not be passed and you
will not be able to access these endpoints.

To use it:
- Login in JupyterHub
- (Optional, if you did not choose the option in the `jupyterhub_config.py` to generate a random token at startup) Upload the `examples/Proxy token manager.ipynb`, run it and create a new token
- Open a terminal and start a server serving on one of the ports you chose (e.g.:  `python -m SimpleHTTPServer 5000`)
- Try to connect to it. If you set it without token check (allow all), you can 
  just go to the correct URL in your browser (e.g. `http://localhost:8000/hub/proxy5000/YOURJUPYTERHUBUSERNAME`). Otherwise, to check using a proxy
  via a AJAX request (that checks that also the CORS headers are properly
  set in the server), use the simple example under `examples/client_ajax_CORS_example.html`: put the correct URL (change the string `USERNAMEHERE`, and possibly change the token, that you can get as
  described above via the Jupyter notebook, or via the link provided in the 
  page, if you have already logged into JupyterHub in the same browser and you have not changed the URL of the `/proxytoken/` endpoint).

### Notes
- If the Docker host is a Mac, you need to start the server to be proxied 
  inside docker on the 0.0.0.0 interface, otherwise Docker will not allow to 
  forward it due to the way networking is configured by default on Docker 
  on the Mac. Note that this is a Docker configuration and not a jhproxy issue.

## License
This code is released under a MIT license.
We acknowledge [nbserverproxy](https://github.com/jupyterhub/nbserverproxy) from
which we have taken free inspiration for the proxy part.
