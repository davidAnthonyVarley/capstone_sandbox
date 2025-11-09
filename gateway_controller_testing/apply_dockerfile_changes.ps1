. .\powershell_scripts\auxiliaryFunctions.ps1
. .\powershell_scripts\variables.ps1

docker build -t $docker_image $dockerfile_path;
minikube image load $docker_image;
printStars;

#edit .yaml files for k8s resources to point to correct microservices
edit_yaml_files -stringToRemove $placeholder -stringToInsert $microservice_name;

deleteAnyExistingResources;
createK8sResource;
getResources;

edit_yaml_files -stringToRemove $microservice_name -stringToInsert $placeholder

createMinikubeTunnel;


