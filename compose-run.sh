#!/bin/bash
docker-compose up -d;

url="http://127.0.0.1:5002"
# Wait for the application to load.
response_code=0;
while [[ $response_code -ne 200 ]]; do
    echo "Waiting..."
    sleep 5
    response_code=$(curl -s -w "%{http_code}" $url -o /dev/null)
done;

echo "Launching the default browser."
echo "If the container is running in Docker, the application will be available at "
echo "$url"

# Launch the default web browser, pointing to the application.
# Check the operating system.
os_name=$(uname -s);
case "$os_name" in
    Linux)
        xdg-open $url
        ;;
    Darwin)
        # MacOS
        open $url
        ;;
    *) # Likely Windows
        start $url
        ;;
esac