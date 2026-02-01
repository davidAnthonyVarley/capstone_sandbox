package main

import (
	"log"
	"net"

	core "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
	extproc "github.com/envoyproxy/go-control-plane/envoy/service/ext_proc/v3"
	"google.golang.org/grpc"
)

type server struct{}


func (s *server) Process(srv extproc.ExternalProcessor_ProcessServer) error {
	for {
		req, err := srv.Recv()
		if err != nil {
			return err
		}

		log.Println("Received a message from Envoy")

		resp := &extproc.ProcessingResponse{}

		// Handle Request Headers
		if headers := req.GetRequestHeaders(); headers != nil {
			log.Println("Processing Request Headers")
			resp = &extproc.ProcessingResponse{
				Response: &extproc.ProcessingResponse_RequestHeaders{
					RequestHeaders: &extproc.HeadersResponse{
						Response: &extproc.CommonResponse{
							HeaderMutation: &extproc.HeaderMutation{
								SetHeaders: []*core.HeaderValueOption{
									{
									    Header: &core.HeaderValue{
									        Key:   "random-header-from-david",
									        RawValue: []byte("this was processed-by-ext-proc yuuup"), // Use RawValue instead of Value: "this was processed-by-ext-proc yuuup",
									    },
									    AppendAction: core.HeaderValueOption_OVERWRITE_IF_EXISTS_OR_ADD, 
									},
								},
							},
						},
					},
				},
			}
		} else if headers := req.GetResponseHeaders(); headers != nil {
			log.Println("Processing Response Headers")
			resp = &extproc.ProcessingResponse{
				Response: &extproc.ProcessingResponse_ResponseHeaders{
					ResponseHeaders: &extproc.HeadersResponse{
						Response: &extproc.CommonResponse{}, // Just continue
					},
				},
			}
		} else {
            // Fallback for any other phases (Body, Trailers, etc.)
			log.Println("Processing other phase - sending default response")
            // You must determine which phase this is to send the correct empty response
            // or modify your EnvoyExtensionPolicy to only send what you handle.
		}

		if err := srv.Send(resp); err != nil {
			return err
		}
	}
}


func main() {
	lis, err := net.Listen("tcp", ":9002")
	if err != nil {
    	log.Fatal(err)
	}

	s := grpc.NewServer()
	extproc.RegisterExternalProcessorServer(s, &server{})
	log.Println("gRPC Server listening on :9002")
	s.Serve(lis)
}