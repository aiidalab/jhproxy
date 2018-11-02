from jhproxy import ProxyHandler, ProxyTokenHandler

c = get_config() # pylint: disable=undefined-variable; # flake8: noqa

## Use the TokenizedDockerSpawner instead of the DockerSpawner
## otherwise you will not have token authentication
c.JupyterHub.spawner_class = 'jhproxy.spawners.TokenizedDockerSpawner'
# Choose your image here
c.DockerSpawner.image = "aiidalab/aiidalab-docker-stack:latest"


# Choose here one of the possible startup configurations (or do not
# specify to use the default)
## - Disable proxy by default
##   c.TokenizedDockerSpawner.default_startup_behavior = "disabled" 
## - Enable proxy without authentication by default
##   c.TokenizedDockerSpawner.default_startup_behavior = "allow_all" 
## - Enable proxy with randomly-generated token authentication by default
c.TokenizedDockerSpawner.default_startup_behavior = "random"

# I show as an example how to proxy more than one port:
# This is not needed of course.
# These are the ports INSIDE the docker container that you want to expose
proxy_ports = [5000, 5001] 

# For how the DockerSpawner currently works, if we have to redefine
# explicitly the jupyter port inside the container if we define 
# additional ports, otherwise JupyterHub will not be able to connect
# to the jupyter notebooks in the spawned containers
# Also use_internal_ip=False is neeed, otherwise port_bindings are overwritten
jupyter_port = 8888
host_ip = '127.0.0.1'
c.DockerSpawner.port = jupyter_port
c.DockerSpawner.use_internal_ip = False
c.DockerSpawner.host_ip = host_ip

## This might not be needed if you expose the ports in your Dockerfile
c.DockerSpawner.extra_create_kwargs.update({
    'ports': [jupyter_port] + proxy_ports
})

# Define the port bindings
# Connect to the host_ip, and let docker choose a random port on the host
# (the proxy will take care at runtime of understanding which port 
# has been mapped to which)
port_bindings = {jupyter_port: (host_ip, )} # At least this MUST be there
# Add custom proxy prts
for proxy_port in proxy_ports:
    port_bindings[proxy_port] = (host_ip, )

c.DockerSpawner.extra_host_config.update({ 
    'port_bindings': port_bindings,
    ## Additional configuration here
    'init': True,
    })

# Define our extra handlers
# Only one proxytoken handler (to get, change tokens) as the token
# is stored in the spawner, so its the same for all ports
extra_handlers = [(r'/proxytoken/', ProxyTokenHandler)] 
for proxy_port in proxy_ports:
    # You can change the URL if you want. Important, however: 
    # 1. if you use more than one proxy_port, give them different names
    # 2. remember to pass the third parameter (even if you have only
    #    one proxy handler) to configure the handler port.
    extra_handlers.append(
        (
            r'/proxy{}/([^/]+)(/.*)'.format(proxy_port), 
            ProxyHandler, 
            dict(proxy_port=proxy_port)
        ),
    )
c.JupyterHub.extra_handlers = extra_handlers

##########################################################################
## Additional, custom configuration below here
## Feel free to change and adapt
##########################################################################

# Additional configuration
c.DockerSpawner.remove_containers = True
c.Spawner.start_timeout = 180
c.Spawner.http_timeout = 120

from jupyter_client.localinterfaces import public_ips
c.JupyterHub.hub_ip = public_ips()[0]

## For debug
#c.JupyterHub.log_level = 'DEBUG'

