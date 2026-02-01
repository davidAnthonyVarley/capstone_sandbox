#i can't build docker images on this machine while virtualbox is the driver for minikube, because it disables some features that wsl needs, and thus that docker needs
#however, minikube does have its own docker installed, so i can transfer the docker file over there, build the image there and that works

minikube cp .\http-1p1-helloworld.py   /home/docker/http-1p1-helloworld/;
minikube cp .\Dockerfile               /home/docker/http-1p1-helloworld/;
minikube cp .\https_client.py          /home/docker/http-1p1-helloworld/;
minikube cp .\build_image.sh           /home/docker/http-1p1-helloworld/;
minikube cp .\requirements.txt         /home/docker/http-1p1-helloworld/;