kubectl delete deployment producer;  
kubectl delete deployment subscriber-pod; 
kubectl apply -f .\microservices\producer_proxy\;  
kubectl apply -f .\microservices\subscriber-pod\;