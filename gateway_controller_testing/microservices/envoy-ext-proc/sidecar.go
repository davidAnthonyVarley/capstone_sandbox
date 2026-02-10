package main

import (
	"bytes"
	"encoding/json"
	//"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings" // Added to join the ID list

	core "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	extproc "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	"google.golang.org/grpc"
)

// Define the struct in sidecar.go so it can parse the response
type MatchResponse struct {
	MatchCount    int      `json:"match_count"`
	SubscriberIDs []string `json:"subscriber_ids"`
}

type server struct{}

// Helper function moved from find_subscribers.go
func find_relevant_subscribers(payload []byte) (*MatchResponse, error) {
	// Ensure this points to your SienaServer port
	url := "http://localhost:8080/match"

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var result MatchResponse
	json.Unmarshal(body, &result)

	return &result, nil
}

func (s *server) Process(srv extproc.ExternalProcessor_ProcessServer) error {
	log.Println(">>> New gRPC stream opened")
	for {
		req, err := srv.Recv()
		if err != nil {
			return err
		}

		resp := &extproc.ProcessingResponse{}

		if headers := req.GetRequestHeaders(); headers != nil {
			log.Println("Processing Request Headers - Identifying Subscribers")

			// 1. Prepare a dummy or extracted payload
			// In a real scenario, you'd extract these values from 'headers'
			//payloadMap := map[string]interface{}{
			//	"price":    600.0,
			//	"category": "hardware",
			//	"location": "NewYork",
			//	"severity": 10.0,
			//	"status":   "active",
			//	"type":     "rain",
			//}
			//payload, _ := json.Marshal(payloadMap)
			allHeaders := make(map[string]string)
    		for _, h := range headers.GetHeaders().GetHeaders() {
    		    allHeaders[h.Key] = h.Value
    		}
		
    		// 2. Get the specific header string
    		eventDataString := allHeaders["x-event-cbr-data"]
		
    		// 3. Convert string to []byte for your matching function
    		payload := []byte(eventDataString)

			// 2. Call the matching logic
			matchResult, err := find_relevant_subscribers(payload)
			
			// Default value if match fails or is empty
			subscriberHeaderValue := "none"
			if err == nil && len(matchResult.SubscriberIDs) > 0 {
				// 3. Convert []string to a single comma-separated string
				subscriberHeaderValue = strings.Join(matchResult.SubscriberIDs, ", ")
			}

			// 4. Mutate headers with the subscriber list
			resp = &extproc.ProcessingResponse{
				Response: &extproc.ProcessingResponse_RequestHeaders{
					RequestHeaders: &extproc.HeadersResponse{
						Response: &extproc.CommonResponse{
							HeaderMutation: &extproc.HeaderMutation{
								SetHeaders: []*core.HeaderValueOption{
									{
										Header: &core.HeaderValue{
											Key:      "x-matched-subscribers",
											RawValue: []byte(subscriberHeaderValue),
										},
										AppendAction: core.HeaderValueOption_OVERWRITE_IF_EXISTS_OR_ADD,
									},
								},
							},
						},
					},
				},
			}
		} else {
			// Handle other phases
			resp = &extproc.ProcessingResponse{
				Response: &extproc.ProcessingResponse_RequestHeaders{
					RequestHeaders: &extproc.HeadersResponse{
						Response: &extproc.CommonResponse{},
					},
				},
			}
		}

		if err := srv.Send(resp); err != nil {
			return err
		}
	}
}

func main() {
	log.Println("hello")
	log.Println("FORCE LOG: Sidecar starting up...")
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
    	log.Fatal(err)
	}

	s := grpc.NewServer()
	extproc.RegisterExternalProcessorServer(s, &server{})
	log.Println("gRPC Server listening on :50051")
	s.Serve(lis)
}