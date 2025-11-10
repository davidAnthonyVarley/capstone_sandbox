$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing"
$powershell_scripts_path = $project_root + "\config_resources\powershell_scripts";
. $powershell_scripts_path\auxiliaryFunctions.ps1;
. $powershell_scripts_path\variables.ps1;

Write-Host "1. Enter minikube's docker daemon" -ForegroundColor Yellow
#minikube image load $docker_image;
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
printStars;
Write-Host "2. Build docker image" -ForegroundColor Yellow
docker build -t $docker_image $dockerfile_path;


#edit .yaml files for k8s resources to point to correct microservices
Write-Host "3. Insert microservice name + port into K8s resource files" -ForegroundColor Yellow
edit_yaml_files -stringToRemove $microservice_placeholder -stringToInsert $microservice_name -muteOutput $true;;
edit_yaml_files -stringToRemove $port_placeholder -stringToInsert $port -muteOutput $true;
#edit_yaml_files -stringToRemove $protocol_placeholder -stringToInsert $protocol;

Write-Host "4. Delete any leftover resources from previous tests" -ForegroundColor Yellow
deleteAnyExistingResources;
Write-Host "5. Create resources" -ForegroundColor Yellow
createK8sResource;
Write-Host "6. Display resources" -ForegroundColor Yellow
getResources;

Write-Host "7. Insert placeholders back into K8s resource files" -ForegroundColor Yellow
edit_yaml_files -stringToRemove $microservice_name -stringToInsert $microservice_placeholder -muteOutput $true;
edit_yaml_files -stringToRemove $port -stringToInsert $port_placeholder  -muteOutput $true;
#edit_yaml_files -stringToRemove $protocol -stringToInsert $protocol_placeholder-muteOutput $true;

Write-Host "8. Create minikube tunnel to expose cluster" -ForegroundColor Yellow
createMinikubeTunnel;


