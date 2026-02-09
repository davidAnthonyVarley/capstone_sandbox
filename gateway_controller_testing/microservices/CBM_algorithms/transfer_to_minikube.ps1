#i can't build docker images on this machine while virtualbox is the driver for minikube, because it disables some features that wsl needs, and thus that docker needs
#however, minikube does have its own docker installed, so i can transfer the docker file over there, build the image there and that works

minikube cp .\        /home/docker/;
#minikube cp .\Dockerfile               /home/docker/;
#minikube cp .\build_images.sh           /home/docker/;