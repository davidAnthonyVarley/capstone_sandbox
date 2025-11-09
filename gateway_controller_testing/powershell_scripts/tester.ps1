. .\auxiliaryFunctions.ps1

$microservice_name = "py-http1p1-helloworld-server";
$placeholder = "MICROSERVICE_NAME_PLACEHOLDER";

edit_yaml_files -stringToInsert $placeholder -stringToRemove $microservice_name
