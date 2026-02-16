#realcurl -vk --http3 "https://www.example.com/mq" --resolve "www.example.com:443:$GATEWAY_HOST";
$GATEWAY_HOST = (minikube ip);
$JSON_PAYLOAD = '{ \"delivery_mode\": \"lightweight_summary\", \"include_metadata\": \"false\", \"data_size\": \"1MB\", \"note\": \"Triggers 1MB response\" }';

realcurl -vk --http3 "https://www.example.com/mq" `
  --resolve "www.example.com:443:$GATEWAY_HOST" `
  -H "x-event-cbr-data: $JSON_PAYLOAD"