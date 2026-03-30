kubectl delete deployment small-sized-data-server-1mb;
kubectl delete deployment medium-sized-data-server-10mb;
kubectl delete deployment large-sized-data-server-100mb;
kubectl delete pv testing-data-pv;
kubectl delete pvc testing-data-pvc;

kubectl apply -f .\microservices\subscriber-pods\testing_data_pv.yaml;
kubectl apply -f .\microservices\subscriber-pods\testing_data_pvc.yaml;
.\reboot_producer_proxy_and_consumer.ps1;
