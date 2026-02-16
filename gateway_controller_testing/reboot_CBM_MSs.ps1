docker build -t davidAnthonyVarley/pst-pod:latest .\microservices\CBM_algorithms\parallel_search_tree\app;
docker build -t davidAnthonyVarley/siena-pod:latest .\microservices\CBM_algorithms\siena\;
docker build -t davidAnthonyVarley/envoy-ext-proc:latest .\microservices\envoy-ext-proc\;

kubectl delete deployment pst-pod;  
kubectl delete svc pst-service;  
kubectl delete deployment siena-pod; 
kubectl delete svc siena-main-service;
kubectl delete envoyextensionpolicy envoy-httpfilter; 
kubectl delete deployment envoycbr-httpfilter-sidecar; 
kubectl delete svc envoycbr-httpfilter-sidecar-service;


kubectl apply -f .\microservices\CBM_algorithms\parallel_search_tree;  
kubectl apply -f .\microservices\CBM_algorithms\siena;
kubectl apply -f .\microservices\envoy-ext-proc\k8s_files;