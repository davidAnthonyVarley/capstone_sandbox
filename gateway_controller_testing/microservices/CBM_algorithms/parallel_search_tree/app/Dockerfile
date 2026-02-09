# Stage 1: Compile the Java source code
FROM eclipse-temurin:17-jdk-alpine AS builder

WORKDIR /app

# Copy all source files and classes (to ensure dependencies are present)
COPY . .

# Compile all .java files in the directory
RUN javac -cp "bin" *.java

# Stage 2: Create the lightweight runtime image
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy only the compiled .class files from the builder stage
COPY --from=builder /app/*.class ./

# Copy the testing_data directory (required for the server to load subscriptions/events)
COPY --from=builder /app/testing_data ./testing_data

# Expose the port (assuming your Server.java uses a port like 8080 or 8081)
EXPOSE 8080

# Run the application starting from Server.class
CMD ["java", "Server"]