function edit_yaml_files {
    param(
        [string]$microservice
    )

    $k8s_resources_folder = ".\k8s_resources\"
    $k8s_resource_files = @("deployment.yaml", "service.yaml",  "gateway.yaml",  "route.yaml")
    foreach ($file in $k8s_resource_files) {
        $yaml_path = $k8s_resources_folder + $file
        (Get-Content $yaml_path) `
        -replace "DEPLOYMENT_NAME", $microservice `
        -replace "APP_LABEL", $microservice |
        Set-Content $yaml_path
    }
}