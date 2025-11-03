docker build -t davidanthonyvarley/fyp-hello-service .;
docker push davidanthonyvarley/fyp-hello-service;

kubectl delete deployments hello-app;
kubectl delete svc hello-app;

kubectl apply -f helloapp_deployment.yaml;
kubectl apply -f helloapp_service.yaml;

kubectl get pods;
kubectl get svc;

minikube service hello-app;