#i can't build docker images on this machine while virtualbox is the driver for minikube, because it disables some features that wsl needs, and thus that docker needs
#however, minikube does have its own docker installed, so i can transfer the docker file over there, build the image there and that works

minikube cp .\sidecar.go     /home/docker/envoy-ext-proc/;
minikube cp .\Dockerfile     /home/docker/envoy-ext-proc/;
minikube cp .\go.sum         /home/docker/envoy-ext-proc/;
minikube cp .\go.mod         /home/docker/envoy-ext-proc/;
minikube cp .\build_image.sh /home/docker/envoy-ext-proc/;