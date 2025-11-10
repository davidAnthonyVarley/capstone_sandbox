#$microservice_name = "py-http1p1-helloworld-server"
#$port = 30080
#$protocol = "HTTP"
$microservice_name = "py-http3-helloworld-server"
$port = 30433;
$protocol = "HTTPS"

#when we want to create a certain microservice with a partiuclar protocol, the placeholders/parameters listed below will be replaced with those actually values 
$microservice_placeholder = "MICROSERVICE_NAME_PLACEHOLDER"
$port_placeholder = "PORT_PLACEHOLDER"
$protocol_placeholder = "PROTOCOL_PLACEHOLDER"


$dockerfile_path = ".\microservices\" + $microservice_name;
$docker_image_name =  "davidanthonyvarley/" + $microservice_name;
$docker_image_tag =  ":latest";
$docker_image = $docker_image_name + $docker_image_tag;

$project_root = "C:\Users\david\capstone_sandbox\gateway_controller_testing"
$k8s_resources_folder = $project_root + "\k8s_resources";
$config_resources_folder = $project_root + "\config_resources";

$https_k8s_secret_name = "http3-tls-cert";