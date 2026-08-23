#!/bin/bash

#script to install all dependencies for MAC/ARM users 
#by alejandro juarez lora

# First, run ./start_chipathon_vnc.sh on a first time to create a container
# then, run ./install_ARM_dependencies.sh
# then, get into de containeer and run /dockerstartup/scripts/run_GL.sh

# Load env variables
export DESIGNS="$(pwd)/designs"
ENVFILE=".env"

if [ -f "${ENVFILE}" ]; then
	source "${ENVFILE}"
fi

if [ -z ${CONTAINER_NAME+z} ]; then
	CONTAINER_NAME="iic-osic-tools_chipathon_xvnc_uid_"$(id -u)
fi

function docker_exec() {
    docker exec -it  --user root ${CONTAINER_NAME} "$@"
}

docker_exec apt-get update
docker_exec apt-get install -y libcurl4-openssl-dev libexpat1-dev libpng-dev
docker_exec apt-get update 
docker_exec apt-get install -y libqhull-dev qhull-bin