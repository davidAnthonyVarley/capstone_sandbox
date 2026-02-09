docker build -t davidAnthonyVarley/pst-pod:latest .\microservices\CBM_algorithms\parallel_search_tree\app;
docker build -t davidAnthonyVarley/siena-pod:latest .\microservices\CBM_algorithms\siena\;

kubectl delete deployment pst-pod;  
kubectl delete svc pst-service;  
kubectl delete deployment siena-pod; 
kubectl delete svc siena-service; 
kubectl apply -f .\microservices\CBM_algorithms\parallel_search_tree;  
kubectl apply -f .\microservices\CBM_algorithms\siena;