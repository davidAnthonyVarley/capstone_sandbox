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
    printStars;
    kubectl create secret tls $https_k8s_secret_name --cert=$project_root\certs\www.example.com.crt --key=$project_root\certs\www.example.com.key --namespace default;
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

function createGateway {
    write-host "Create new Gateway with this name"  -Foreground Cyan
    kubectl apply -f $k8s_resources_folder\gateway.yaml -n default;
    printStars;
}


function deleteGateway {
    write-host "Delete any existing $microservice_name gateway"  -Foreground Cyan
    kubectl delete gateway ($microservice_name + "-gateway");
    printStars;
}

function createRoutes{
    write-host "Create new HTTP and UDP Routes with this name"  -Foreground Cyan
    kubectl apply -f $k8s_resources_folder\HTTProute.yaml;
    kubectl apply -f $k8s_resources_folder\UDProute.yaml;
    printStars;
}


function deleteRoutes {
    write-host "Delete any existing $microservice_name http and udp routes"  -Foreground Cyan
    kubectl delete httproute ($microservice_name + "-http-route");
    kubectl delete udproute  ($microservice_name + "-uddp-route");
    printStars;
}