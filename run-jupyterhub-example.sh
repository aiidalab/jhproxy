#!/bin/bash
if [ -e examples/jupyterhub_config.py ]
then
    jupyterhub -f examples/jupyterhub_config.py
else
    echo "jupyterhub_config.py not found, probably your are not calling this script from its directory?"
    exit 1
fi
