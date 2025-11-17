$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing";
$powershell_scripts_path = $project_root + "\powershell_scripts";
. $powershell_scripts_path\variables;


$port = -1;
switch ($microservice_name) {
    "http-1p1-helloworld" {
        $port = 30000;
    }
    "https-1p1-helloworld" {
        $port = 30001;
    }
    "https-2-helloworld" {
        $port = 30002;
    }
    "https-3-helloworld" {
        $port = 30003;
    }
}

#when we want to create a certain microservice with a partiuclar protocol, the placeholders/parameters listed below will be replaced with those actually values 
$microservice_placeholder = "MICROSERVICE_NAME_PLACEHOLDER"
$port_placeholder = "PORT_PLACEHOLDER"
$protocol_placeholder = "PROTOCOL_PLACEHOLDER"


$dockerfile_parent_folder_path = $project_root + "\microservices\" + $microservice_name;
$dockerfile_path = $dockerfile_parent_folder_path + "\Dockerfile";
$docker_image_name =  "davidanthonyvarley/" + $microservice_name;
$docker_image_tag =  ":latest";
$docker_image = $docker_image_name + $docker_image_tag;

$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing"
$k8s_resources_folder = $project_root + "\k8s_resources";
$config_resources_folder = $project_root + "\config_resources";

$https_k8s_secret_name = "http3-tls-cert";