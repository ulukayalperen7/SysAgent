# Use an official OpenJDK runtime as a parent image
FROM openjdk:17-jdk-slim

# Set the working directory in the container
WORKDIR /app

# Copy the wrapper and settings
COPY mvnw .
COPY mvnw.cmd .
COPY .mvn .mvn
COPY pom.xml .

# Grant execute permission to mvnw
RUN chmod +x mvnw

# Resolve dependencies (this will be cached if pom.xml doesn't change)
RUN ./mvnw dependency:go-offline

# Copy the source code
COPY src src

# Build the application
RUN ./mvnw clean package -DskipTests

# Run the jar file
# Adjust the jar name based on your pom.xml version
ENTRYPOINT ["java","-jar","target/sysagent-backend-0.0.1-SNAPSHOT.jar"]
