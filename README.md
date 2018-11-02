# jhproxy

A port proxy for JupyterHub when using the DockerSpawner, optionally with 
authentication.

If you use JupyterHub, and the app inside the jupyter notebook opens a port 
(e.g. ) ...

## Documentation

- Limitations: only DockerSpawner

- If you configure properly in `jupyterhub_config.py`, you don't even
  need to expose ports in the Dockerfile of the image

- If the host is a Mac, you need to start the API inside docker on the 0.0.0.0
  interface, otherwise Docker will not allow to forward it due to the
  way networking is configured by default on Docker on the Mac. Note that this
  is a Docker configuration and not a jhproxy issue.


### Setup with authorization


### Setup with authorization


## License
