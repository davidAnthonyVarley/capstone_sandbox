package main

import (
	"context"
	"fmt"
	"log"

	core "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	extproc "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	// 1. Set up a connection to the gRPC server
	conn, err := grpc.Dial("localhost:9002", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()

	client := extproc.NewExternalProcessorClient(conn)

	// 2. Open the bidirectional stream
	stream, err := client.Process(context.Background())
	if err != nil {
		log.Fatalf("could not open stream: %v", err)
	}

	// 3. Create a RequestHeaders message
	// Note: We use HttpHeaders here, which is what the protobuf expects
// 3. Create a RequestHeaders message with the JSON payload in the correct hierarchy
	req := &extproc.ProcessingRequest{
		Request: &extproc.ProcessingRequest_RequestHeaders{
			RequestHeaders: &extproc.HttpHeaders{
				Headers: &core.HeaderMap{
					Headers: []*core.HeaderValue{
						{
							Key:   "x-event-cbr-data",
							Value: `{"price": 600.0, "category": "hardware", "location": "NewYork", "severity": 10.0, "status": "active", "type": "rain"}`,
						},
					},
				},
			},
		},
	}

	// 4. Send the request
	fmt.Println("Sending RequestHeaders to sidecar...")
	if err := stream.Send(req); err != nil {
		log.Fatalf("failed to send: %v", err)
	}

	// 5. Receive the response
	resp, err := stream.Recv()
	if err != nil {
		log.Fatalf("failed to receive: %v", err)
	}

	// 6. Inspect the mutated headers
	// Your sidecar.go responds with a RequestHeaders processing phase
	if h := resp.GetRequestHeaders(); h != nil {
		// Navigation: Response -> CommonResponse -> HeaderMutation -> SetHeaders
		mutations := h.GetResponse().GetHeaderMutation().GetSetHeaders()
		if len(mutations) == 0 {
			fmt.Println("No header mutations received.")
		}
		for _, m := range mutations {
			fmt.Printf("Header Mutated: %s = %s\n", m.Header.Key, string(m.Header.RawValue))
		}
	} else {
		fmt.Println("Received response, but it wasn't a RequestHeaders mutation.")
	}
}