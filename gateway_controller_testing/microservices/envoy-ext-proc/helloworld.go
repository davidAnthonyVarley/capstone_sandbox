package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// MatchResponse matches the structure of the JSON sent by Java
type MatchResponse struct {
	MatchCount    int      `json:"match_count"`
	SubscriberIDs []string `json:"subscriber_ids"`
}

func main() {
	url := "http://localhost:8080/match"
	payload := []byte(`{"price":600.0,"category":"hardware","location":"NewYork","severity":10.0,"status":"active","type":"rain"}`)

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		fmt.Printf("Request failed: %s\n", err)
		return
	}
	defer resp.Body.Close()

	// Read the body
	body, _ := io.ReadAll(resp.Body)

	// Parse (Unmarshal) the JSON into our struct
	var result MatchResponse
	if err := json.Unmarshal(body, &result); err != nil {
		fmt.Println("Error parsing JSON:", err)
		return
	}

	// Now you can access individual fields easily
	fmt.Printf("Total Matches: %d\n", result.MatchCount)
	fmt.Println("Subscriber List:")
	for _, id := range result.SubscriberIDs {
		fmt.Printf(" -> Found ID: %s\n", id)
	}
}