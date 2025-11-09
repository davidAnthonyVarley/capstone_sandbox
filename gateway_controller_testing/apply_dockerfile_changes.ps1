. .\auxiliaryFunctions.ps1

#$microservice = "http3-py-server"
$microservice_name = "py-http1p1-helloworld-server"
$dockerfile_path = ".\microservices\" + $microservice_name;
$docker_image_name =  "davidanthonyvarley/" + $microservice_name;
$docker_image_tag =  ":latest";
$docker_image = $docker_image_name + $docker_image_tag;

#edit .yaml files for k8s resources to point to correct microservices

edit_yaml_files -microservice $microservice_name

docker build -t $docker_image $dockerfile_path;

minikube image load $docker_image;

kubectl delete deployments $microservice_name;
kubectl delete svc $microservice_name;

kubectl apply -f k8s_files\helloapp_deployment.yaml;
kubectl apply -f k8s_files\helloapp_service.yaml;

kubectl get pods;
kubectl get svc;

kubectl wait --for=condition=ready pod -l app=$microservice_name --timeout=30s
minikube service $microservice_name;