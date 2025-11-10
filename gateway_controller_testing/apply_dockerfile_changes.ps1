. .\powershell_scripts\auxiliaryFunctions.ps1
. .\powershell_scripts\variables.ps1

docker build -t $docker_image $dockerfile_path;
minikube image load $docker_image;
printStars;

#edit .yaml files for k8s resources to point to correct microservices
edit_yaml_files -stringToRemove $microservice_placeholder -stringToInsert $microservice_name;
edit_yaml_files -stringToRemove $port_placeholder -stringToInsert $port;
edit_yaml_files -stringToRemove $protocol_placeholder -stringToInsert $protocol;

deleteAnyExistingResources;
createK8sResource;
getResources;

edit_yaml_files -stringToRemove $microservice_name -stringToInsert $microservice_placeholder;
edit_yaml_files -stringToRemove $port -stringToInsert $port_placeholder;
edit_yaml_files -stringToRemove $protocol -stringToInsert $protocol_placeholder;

createMinikubeTunnel;


