$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing"
$powershell_scripts_path = $project_root + "\powershell_scripts";
. $powershell_scripts_path\variables.ps1;
. $powershell_scripts_path\constants.ps1;

function printStars {
    write-host "*"
    #write-host "*"
    #write-host "*"
}
function createHTTPSSecret {
    write-host "Create new HTTPS Secret" -Foreground Cyan
    kubectl create secret tls $https_k8s_secret_name --cert=$project_root\certs\cert.pem --key=$project_root\certs\key.pem --namespace default;
    printStars;
}
function deleteHTTPSSecret {
    write-host "Delete any existing HTTPS Secret"  -Foreground Cyan
    kubectl delete secret $https_k8s_secret_name;
    printStars;
}

function createDeployments {
    write-host "Create new Deployment with this name"  -Foreground Cyan
    kubectl apply -f $k8s_resources_folder\deployment.yaml -n default;
    printStars;
}


function deleteDeployments {
    write-host "Delete any existing $microservice_name Deployment"  -Foreground Cyan
    kubectl delete deployments $microservice_name;
    printStars;
}

function createServices {
    write-host "Create new Service with this name"  -Foreground Cyan
    kubectl apply -f $k8s_resources_folder\service.yaml -n default;
    printStars;
}

function deleteServices {
    write-host "Delete any existing $microservice_name Service"  -Foreground Cyan
    kubectl delete svc $microservice_name;
    printStars;
}