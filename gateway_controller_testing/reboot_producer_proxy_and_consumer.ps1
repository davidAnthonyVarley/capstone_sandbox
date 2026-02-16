kubectl delete deployment producer;  
kubectl delete deployment small-sized-data-server--1mb; 
kubectl apply -f .\microservices\producer_proxy\;  
kubectl apply -f .\microservices\subscriber-pods\small_sized_data__server\;