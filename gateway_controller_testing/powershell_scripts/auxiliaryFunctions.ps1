$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing"
$powershell_scripts_path = $project_root + "\powershell_scripts";
. $powershell_scripts_path\manageK8sResources.ps1;
. $powershell_scripts_path\variables.ps1;
. $powershell_scripts_path\constants.ps1;

function buildDockerImage {

    edit_file -path $dockerfile_path -stringToRemove $microservice_placeholder -stringToInsert $microservice_name  -muteOutput $true;
    Write-Host "";
    edit_file -path $dockerfile_path -stringToRemove $port_placeholder -stringToInsert $port  -muteOutput $true;

    docker build -t $docker_image $dockerfile_parent_folder_path;
    printStars;

    edit_file -path $dockerfile_path -stringToRemove $microservice_name -stringToInsert $microservice_placeholder  -muteOutput $true;
    Write-Host "";
    edit_file -path $dockerfile_path -stringToRemove $port -stringToInsert $port_placeholder  -muteOutput $true;
}
function getResources {
    write-host "Display Pods"  -Foreground Cyan
    kubectl get pods -n default;
    printStars
    write-host "Display Services"  -Foreground Cyan
    kubectl get svc -n default;
    printStars;
    write-host "Display name of HTTPS Secret"  -Foreground Cyan
    kubectl get secret $https_k8s_secret_name -n default -o name
    printStars;
    
}

function createMinikubeTunnel {
    kubectl wait --for=condition=ready pod -l app=$microservice_name --timeout=45s

    write-host "**"
    write-host "Access the app on" 
    Write-Host "        http://localhost:$port" -ForegroundColor Green -NoNewline
    Write-Host " (if HTTP microservice)"
    write-host "or"
    write-host "        https://localhost:$port" -ForegroundColor Green -NoNewline
    Write-Host " (if HTTPS microservice)"
    write-host "**"

    #kubectl port-forward "service/$microservice_name" ("$port"+":"+"$port");
    minikube service $microservice_name;
    #$minikubeURLs = minikube service $microservice_name --url;
#
    #write-host "//"
    #write-host $minikubeURLs
    #write-host "//"

    #foreach ()
}

function createK8sResource {
    createHTTPSSecret;
    createDeployments;
    createServices;
}
function deleteAnyExistingResources {
    deleteHTTPSSecret;
    deleteDeployments;
    deleteServices;
}


function edit_yaml_files {
    param(
        [string]$stringToRemove,
        [string]$stringToInsert,
        [boolean]$muteOutput
    )
    
    Write-Host "Replace"
    Write-Host $stringToRemove
    Write-Host "in .yaml files and Dockerfile with"
    Write-Host $stringToInsert
    Write-Host "in"
    Write-Host $k8s_resources_folder
    Write-Host "+"
    Write-Host $dockerfile_path;

    $k8s_resource_files = @("\deployment.yaml", "\service.yaml",  "\gateway.yaml",  "\route.yaml");
    foreach ($file in $k8s_resource_files) {
        $yaml_path = $k8s_resources_folder + $file;

        edit_file -path $yaml_path -stringToInsert $stringToInsert -stringToRemove $stringToRemove -muteOutput $muteOutput;
    }

    printStars;
}

function edit_file {
    param(
        [string]$path,
        [string]$stringToRemove,
        [string]$stringToInsert,
        [boolean]$muteOutput
    )

    (Get-Content $path) `
    -replace $stringToRemove, $stringToInsert ` |
    Set-Content $path;

    if (-not $muteOutput) {
        Get-Content $path
    }
}
