$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing\"
$k8s_resources_folder = $project_root + "k8s_resources\";
function printStars {
    write-host "*"
    write-host "*"
    write-host "*"
}

function createK8sResource {
    write-host "Create new Deployment with this name"
    kubectl apply -f $k8s_resources_folder\deployment.yaml -n default;
    printStars;
    write-host "Create new Service with this name"
    kubectl apply -f $k8s_resources_folder\service.yaml -n default;;
    printStars;
}
function getResources {

    write-host "Display Pods"
    kubectl get pods -n default;
    write-host "Display Services"
    kubectl get svc -n default;;
    printStars;
}

function createMinikubeTunnel {
    kubectl wait --for=condition=ready pod -l app=$microservice_name --timeout=30s
    minikube service $microservice_name;
}

function deleteAnyExistingResources {
    kubectl delete deployments $microservice_name;
    write-host "Delete existing Deployment with this name"
    printStars;
    kubectl delete svc $microservice_name;
    write-host "Delete existing Service with this name"
    printStars;
}

function edit_yaml_files {
    param(
        [string]$stringToRemove,
        [string]$stringToInsert
    )
    write-host "Replace\n$stringToRemove\n in .yaml files with \n$stringToInsert\n in \n$k8s_resources_folder";

    $k8s_resource_files = @("deployment.yaml", "service.yaml",  "gateway.yaml",  "route.yaml");
    foreach ($file in $k8s_resource_files) {
        $yaml_path = $k8s_resources_folder + $file;

        (Get-Content $yaml_path) `
        -replace $stringToRemove, $stringToInsert ` |
        Set-Content $yaml_path;
    }
    printStars;
}
