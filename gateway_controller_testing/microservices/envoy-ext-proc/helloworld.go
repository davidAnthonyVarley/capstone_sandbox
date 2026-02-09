package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
)

// MatchResponse matches the schema you set up in SienaServer.java
type MatchResponse struct {
	MatchCount    int      `json:"match_count"`
	SubscriberIDs []string `json:"subscriber_ids"`
}

func handleIncomingRequest(w http.ResponseWriter, r *http.Request) {
	// 1. Extract parameters from the URL
	// Example URL: /mq?price=600&category=hardware&location=NewYork&severity=10&status=active&type=rain
	query := r.URL.Query()

	// 2. Parse values and handle types (converting strings to floats where necessary)
	price, _ := strconv.ParseFloat(query.Get("price"), 64)
	severity, _ := strconv.ParseFloat(query.Get("severity"), 64)

	// 3. Create a map that matches your JSON payload structure
	payloadMap := map[string]interface{}{
		"price":    price,
		"category": query.Get("category"),
		"location": query.Get("location"),
		"severity": severity,
		"status":   query.Get("status"),
		"type":     query.Get("type"),
	}

	// 4. Convert map to JSON bytes
	payload, _ := json.Marshal(payloadMap)

	// 5. Forward to your subscriber matching logic
	result, err := find_relevant_subscribers(payload)
	if err != nil {
		http.Error(w, "Match failed", 500)
		return
	}

	// 6. Return the results to the original caller
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func find_relevant_subscribers(payload []byte) (*MatchResponse, error) {
	// Use port 8081 as defined in your SienaServer.java
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

func main() {
	http.HandleFunc("/mq", handleIncomingRequest)
	fmt.Println("Gateway listening on :8070...")
	http.ListenAndServe(":8070", nil)
}

//example query:
//# Update the resolve mapping from 443 to 8070
//realcurl -vk --http3 "https://www.example.com/mq" --resolve "www.example.com:443:127.0.0.1:8070"