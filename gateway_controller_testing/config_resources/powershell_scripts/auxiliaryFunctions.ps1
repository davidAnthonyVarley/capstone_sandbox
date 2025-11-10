$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing"
$powershell_scripts_path = $project_root + "\config_resources\powershell_scripts";
. $powershell_scripts_path\manageK8sResources.ps1;
. $powershell_scripts_path\variables.ps1;

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
    kubectl wait --for=condition=ready pod -l app=$microservice_name --timeout=30s
    minikube service $microservice_name;
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
    Write-Host "in .yaml files with"
    Write-Host $stringToInsert
    Write-Host "in"
    Write-Host $k8s_resources_folder

    $k8s_resource_files = @("\deployment.yaml", "\service.yaml",  "\gateway.yaml",  "\route.yaml");
    foreach ($file in $k8s_resource_files) {
        $yaml_path = $k8s_resources_folder + $file;

        (Get-Content $yaml_path) `
        -replace $stringToRemove, $stringToInsert ` |
        Set-Content $yaml_path;

        if (-not $muteOutput) {
            Get-Content $yaml_path
        }
    }
    printStars;
}
