# Use the official Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install required build tools and dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libsndfile1 \
    libsndfile1-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Copy the start_services.sh script and supervisord.conf into the container
COPY start_services.sh /app/start_services.sh
COPY supervisord.conf /etc/supervisord.conf
RUN chmod +x /app/start_services.sh

# Expose the ports the app runs on
EXPOSE 9000
EXPOSE 8002

# Run the application with the entry point script
CMD ["/app/start_services.sh"]
