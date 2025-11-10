#$microservice_name = "py-http1p1-helloworld-server"
$microservice_name = "py-http3-helloworld-server"
$microservice_placeholder = "MICROSERVICE_NAME_PLACEHOLDER"
$port = 34433
$port_placeholder = "PORT_PLACEHOLDER"
$protocol = "HTTP3"
$protocol_placeholder = "PROTOCOL_PLACEHOLDER"


$dockerfile_path = ".\microservices\" + $microservice_name;
$docker_image_name =  "davidanthonyvarley/" + $microservice_name;
$docker_image_tag =  ":latest";
$docker_image = $docker_image_name + $docker_image_tag;