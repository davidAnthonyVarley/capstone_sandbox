FROM golang:1.24-alpine AS builder

WORKDIR /app

# Copy go.mod and go.sum
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the rest of the source code
COPY . .

# NEW STEP: Fix any missing dependency links
RUN go mod tidy

# --- CHANGE IS HERE ---
# We add CGO_ENABLED=0 to disable C links
# We add GOOS=linux to ensure the target is Linux
RUN CGO_ENABLED=0 GOOS=linux go build -o sidecar .

# Final stage
FROM alpine:3.18
RUN adduser -D -g '' appuser
USER appuser

COPY --from=builder /app/sidecar /sidecar

EXPOSE 9002
ENTRYPOINT ["/sidecar"]