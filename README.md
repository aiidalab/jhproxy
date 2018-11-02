# jhproxy

A safe way to proxy ports from docker containers running inside a JupyterHub to the outside world.

## Features

The JupyterHub administrator can:

 * select which ports can be forwarded
 * select whether to protect access to forwarded ports by tokens or not  
   (when access protected, tokens are provided by `X-Proxy-Token` HTTP header)

A user logged in to the JupyterHub can:

 * get his or her current proxy token via a `GET` request to `http(s)://<JUPYTERHUBHOST>/hub/proxytoken/`
 * disable or regenerate his or her proxy token via a `POST` request to `http(s)://<JUPYTERHUBHOST>/hub/proxytoken/`

An internet user can:

* access the proxied service at `http(s)://<JUPYTERHUBHOST>/hub/proxy/<PORT>/<USER>`



## Limitations

 * works (only) with `DockerSpawner` so far (extended to `jhproxy.spawners.TokenizedDockerSpawner`)

## Background

**Use case:** As the JupyterHub user Bob, you are running a service in your environment (say, a web server running
on port `5000`). You would like to give your friend Alice (or even the entire world) access to this service
without giving them access to your entire JupyterHub account.

**Problem 1:** By default, even you as the user running the service have no way of accessing the service by typing a URL into your browser.
This problem is solved by the [nbserverproxy](https://github.com/jupyterhub/nbserverproxy) jupyter notebook server extension,
which makes your service available to *you* under `http(s)://<JUPYTERHUBHOST>/user/bob/proxy/5000`

**Problem 2:** Now *you* can access the service from your browser, but your
friend Alice still can't - because she is not logged in to your account.  This
problem is solved by `jhproxy`, which makes the service available at
`http(s)://<JUPYTERHUBHOST>/hub/proxy/5000/bob`,
either publicly to everyone or protected by a "proxy token".


## Installation

On the machine where JupyterHub is installed:

1. `pip install jhproxy`

2. adjust your `jupyterhub_config.py`, specifying
   - which ports to proxy
   - under which address
   - whether to protect access via proxy tokens
   - whether to generate a random proxy token at startup
   - ...

Please check out a fully documented working example in `examples/jupyterhub_config.py`.
Feel free to copy, reuse and edit to your needs.

**Notes:**
 - If the Docker host is a Mac, you need to start the server to be proxied
   inside docker on the 0.0.0.0 interface, otherwise Docker will not allow to
   forward it due to the way networking is configured by default on Docker on the
   Mac. Note that this is an issue of the Docker configuration, not of jhproxy.
 - If you don't need authorization, you can just use the standard `DockerSpawner` and ports will simply be proxied. If you instead want authorization, use `jbproxy.spawners.TokenizedDockerSpawner`
  as in the configuration example.

## Usage

In the following, we assume you are logged in as a user to a JupyterHub
with `jhproxy` enabled (see installation section). This **won't** work when
running a simple stand-alone jupyter notebook server or when running inside a JupyterHub that does not have `jhproxy` enabled.

### No authorization (allow all)

 * open a terminal and start your service (e.g.: `python -m SimpleHTTPServer 5000`)
 * try to connect to it at `http(s)://<JUPYTERHUBHOST>/user/bob/proxy/5000`  

### Authorization via proxy token

 * open a terminal and start your service (e.g.: `python -m SimpleHTTPServer 5000`)
 * open a terminal and clone this repository
 * open the `examples/token_demo.ipynb` notebook in jupyter
 * run the HTML code cell
 * press the button to get a token from
   `http(s)://<JUPYTERHUBHOST>/hub/proxytoken/`
 * try to connect to your service at `http(s)://<JUPYTERHUBHOST>/user/bob/proxy/5000`  ,
   now providing the proxy token in the `X-Proxy-Token` HTTP header  

See `examples/client_ajax_CORS.html` for an example of how to do the last step via an AJAX request that also checks whether the CORS headers of the server are properly configured.
Make sure to put the correct URL, change the string `USERNAMEHERE`, and the token.

## License
This code is released under the MIT license.

We acknowledge [nbserverproxy](https://github.com/jupyterhub/nbserverproxy)
for inspiration for the proxy component.
