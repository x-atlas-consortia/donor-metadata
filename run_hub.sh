#!/bin/bash
echo "**************************************************************"
echo "HuBMAP/SenNet Donor Metadata Curation Application start script"
echo "**************************************************************"
echo ""
echo "Removing prior containers for this application..."
# Remove any prior instances of the container.
docker stop donor-metadata-local > /dev/null 2>&1
docker rm donor-metadata-local > /dev/null 2>&1

# Run the container based on the Docker Hub image.
echo "Starting application..."
docker run -d --rm --name donor-metadata -p 5002:5002 hubmap/donor-metadata;

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
