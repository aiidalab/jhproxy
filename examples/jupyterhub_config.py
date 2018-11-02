from jupyter_client.localinterfaces import public_ips

from jhproxy import ProxyHandler, ProxyTokenHandler

c = get_config() # pylint: disable=undefined-variable; # flake8: noqa
# # user Docker Spawner
c.JupyterHub.spawner_class = 'jhproxy.spawners.TokenizedDockerSpawner'
c.DockerSpawner.image = "aiidalab/aiidalab-docker-stack:latest"

# Possible startup configurations
## Disable proxy by default
#c.TokenizedDockerSpawner.default_startup_behavior = "disabled" 
## Enable proxy without authentication by default
#c.TokenizedDockerSpawner.default_startup_behavior = "allow_all" 
## Enable proxy with randomly-generated token authentication by default
c.TokenizedDockerSpawner.default_startup_behavior = "random"

jupyter_port = 8888
proxy_port = 5000
host_ip = '127.0.0.1'

c.DockerSpawner.port = jupyter_port
# These two are needed otherwise the port_bindings are overwritten
c.DockerSpawner.use_internal_ip = False
c.DockerSpawner.host_ip = host_ip

c.DockerSpawner.extra_create_kwargs.update({
    'ports': [jupyter_port, proxy_port] # Expose these ports
})
c.DockerSpawner.extra_host_config.update({ 
    'init': True,
    'port_bindings': {jupyter_port: (host_ip, ), proxy_port: (host_ip, )}
    })

c.JupyterHub.extra_handlers = [
    (r'/proxy/([^/]+)(/.*)', ProxyHandler, dict(proxy_port=proxy_port)),
    #(r'/proxydebug/(.*)', ProxyDebugHandler)
    (r'/proxytoken/', ProxyTokenHandler),
    ]



c.DockerSpawner.remove_containers = True
c.Spawner.start_timeout = 180
c.Spawner.http_timeout = 120

c.JupyterHub.hub_ip = public_ips()[0] # default loopback port doesn't work

## For debug
c.JupyterHub.log_level = 'DEBUG'

