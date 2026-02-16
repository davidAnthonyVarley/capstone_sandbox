#realcurl -vk --http3 "https://www.example.com/mq" --resolve "www.example.com:443:$GATEWAY_HOST";
$GATEWAY_HOST = (minikube ip);
$JSON_PAYLOAD = '{\"price\": 600.0, \"category\": \"hardware\", \"location\": \"NewYork\", \"severity\": 10.0, \"status\": \"active\", \"type\": \"rain\"}';

realcurl -vk --http3 "https://www.example.com/mq" `
  --resolve "www.example.com:443:$GATEWAY_HOST" `
  -H "x-event-cbr-data: $JSON_PAYLOAD"