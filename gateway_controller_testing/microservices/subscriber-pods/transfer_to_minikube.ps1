#i can't build docker images on this machine while virtualbox is the driver for minikube, because it disables some features that wsl needs, and thus that docker needs
#however, minikube does have its own docker installed, so i can transfer the docker file over there, build the image there and that works

minikube cp .\subscriber-pod.py        /home/docker/subscriber-pod/;
minikube cp .\Dockerfile               /home/docker/subscriber-pod/;
minikube cp .\build_image.sh           /home/docker/subscriber-pod/;
minikube cp .\requirements.txt         /home/docker/subscriber-pod/;