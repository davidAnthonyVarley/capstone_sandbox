kubectl delete deployment producer;  
kubectl delete deployment small-sized-data-server--1mb; 
kubectl delete deployment medium-sized-data-server--10mb; 
kubectl delete deployment large-sized-data-server--100mb; 
kubectl apply -f .\microservices\producer_proxy\;  
kubectl apply -f .\microservices\subscriber-pods\small_sized_data__server\;
kubectl apply -f .\microservices\subscriber-pods\medium_sized_data__server\;
kubectl apply -f .\microservices\subscriber-pods\large_sized_data__server\;
