#!/bin/bash
echo "**************************************************************"
echo "HuBMAP/SenNet Donor Metadata Curation Application start script"
echo "**************************************************************"
echo ""
echo "Removing prior containers for this application..."
# Remove any prior instances of the container.
docker stop donor-metadata-local > /dev/null 2>&1
docker rm donor-metadata-local > /dev/null 2>&1

# Set path to external bind mount to the cfg directory that contains the app.cfg file.
# The assumption is that the app.cfg file is in the current directory.

# Get relative path to current directory.
base_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# Convert to absolute path.
base_dir="$(cd -- "$base_dir" && pwd -P;)"
echo "base_dir = $base_dir"

config_file="app.cfg"
if [ ! -e "$config_file" ]
then
  echo "Error: No configuration file at $config_file."
  exit;
fi

# Run the container locally.
# Port 5002 is the port for a local instance.
echo "Starting application..."
docker run \
  -d \
  --rm \
  --name donor-metadata-local \
  -v "$base_dir":/usr/src/app/instance\
  -p 5002:5002 hmsn/donor-metadata-local;

url="http://127.0.0.1:5000"
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
