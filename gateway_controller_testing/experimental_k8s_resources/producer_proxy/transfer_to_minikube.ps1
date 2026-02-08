#i can't build docker images on this machine while virtualbox is the driver for minikube, because it disables some features that wsl needs, and thus that docker needs
#however, minikube does have its own docker installed, so i can transfer the docker file over there, build the image there and that works

minikube cp .\RabbitConfig.java        /home/docker/producer_proxy/;
minikube cp .\Dockerfile               /home/docker/producer_proxy/;
minikube cp .\ProducerController.java  /home/docker/producer_proxy/;
minikube cp .\build_image.sh           /home/docker/producer_proxy/;
minikube cp .\application.properties   /home/docker/producer_proxy/;
minikube cp .\producer.py              /home/docker/producer_proxy/;