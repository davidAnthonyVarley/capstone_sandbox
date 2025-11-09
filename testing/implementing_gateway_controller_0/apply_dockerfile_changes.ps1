$ms_path = ".\microservices\py_flask_server\";

docker build -t davidanthonyvarley/fyp-hello-service:latest $ms_path;

minikube image load davidanthonyvarley/fyp-hello-service:latest;

kubectl delete deployments hello-app;
kubectl delete svc hello-app;

kubectl apply -f k8s_files\helloapp_deployment.yaml;
kubectl apply -f k8s_files\helloapp_service.yaml;

kubectl get pods;
kubectl get svc;

minikube service hello-app;