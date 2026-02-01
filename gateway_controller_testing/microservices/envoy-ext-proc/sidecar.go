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

		// Check if this is the "Request Headers" phase
		if headers := req.GetRequestHeaders(); headers != nil {
			resp := &extproc.ProcessingResponse{
				Response: &extproc.ProcessingResponse_RequestHeaders{
					RequestHeaders: &extproc.HeadersResponse{
						Response: &extproc.CommonResponse{
							HeaderMutation: &extproc.HeaderMutation{
								SetHeaders: []*core.HeaderValueOption{
									{
										Header: &core.HeaderValue{
											Key:   "x-custom-header",
											Value: "processed-by-ext-proc",
										},
									},
								},
							},
						},
					},
				},
			}
			srv.Send(resp)
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