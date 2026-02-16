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
	// Updated URL to the one you verified
	url := "http://pst-service:8080/match"
	//url := "http://localhost:8080/match"

	log.Printf("Sidecar: Sending payload to Siena: %s", string(payload))

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		log.Printf("Sidecar ERROR: Failed to reach pst-service: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	log.Printf("Sidecar: Received raw response from Siena: %s", string(body))

	var result MatchResponse
	if err := json.Unmarshal(body, &result); err != nil {
		log.Printf("Sidecar ERROR: Failed to unmarshal JSON: %v", err)
		return nil, err
	}

	return &result, nil
}

func (s *server) Process(srv extproc.ExternalProcessor_ProcessServer) error {
	log.Println(">>> New gRPC stream opened")
	for {
		req, err := srv.Recv()
		if err != nil {
			return err
		}

		// --- NEW: EXTRACTION OF ATTRIBUTES ---
		// This captures the source.address and request.path you added to YAML
		//attrs := req.GetAttributes()
		//if attrs != nil {
		//	if addr, ok := attrs["source.address"]; ok {
		//		log.Printf("Sidecar: Attribute [source.address] = %s", addr.GetFields()["value"].GetStringValue())
		//	}
		//}

		resp := &extproc.ProcessingResponse{}

		if headers := req.GetRequestHeaders(); headers != nil {
			log.Println("Processing Request Headers - Identifying Subscribers")

			allHeaders := make(map[string]string)
			for _, h := range headers.GetHeaders().GetHeaders() {
			    log.Printf("Sidecar: Received Header-value [%s]", h)
			    log.Printf("Sidecar: Received h.GetKey() [%s]",h.GetKey())
			    log.Printf("Sidecar: Received h.GetValue() [%s]",h.GetValue())

			    k := h.GetKey()
			
			    // 1. Try to get the string value first
			    v := h.GetValue()
			
			    // 2. If it's empty, check the RawValue (bytes)
			    if v == "" && len(h.GetRawValue()) > 0 {
			    	log.Printf("v == '' && len(h.GetRawValue()) > 0, so try to stringify raw bytes")

			        v = string(h.GetRawValue()) // Convert []byte to string
			    	log.Printf("stringified raw bytes == [%s]", v)

			    }
			
			    log.Printf("Sidecar: Received Header [%s] = [%s]", k, v)
			
			    // 3. Store in the map (lowercase keys are safer for lookups)
			    allHeaders[strings.ToLower(k)] = v
			}
			
			// Use lowercase key check for safety
			eventDataString := allHeaders["x-event-cbr-data"]
			if eventDataString == "" {
				log.Println("Sidecar WARNING: x-event-cbr-data header is MISSING or EMPTY")
			}
		
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
	lis, err := net.Listen("tcp", ":9002")
	if err != nil {
    	log.Fatal(err)
	}

	s := grpc.NewServer()
	extproc.RegisterExternalProcessorServer(s, &server{})
	log.Println("gRPC Server listening on :9002")
	s.Serve(lis)
}