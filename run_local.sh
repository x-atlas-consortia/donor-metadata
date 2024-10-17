#!/bin/bash
echo "**************************************************************"
echo "HuBMAP/SenNet Donor Metadata Curation Application start script"
echo "**************************************************************"
echo ""
echo "Removing prior containers for this application..."
# Remove any prior instances of the container.
docker stop donor-metadata-local > /dev/null 2>&1
docker rm donor-metadata-local > /dev/null 2>&1

# Set path to external volume that contains the app.cfg file.
# The assumption is that the external volume is the current directory.

# Get relative path to current directory.
base_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# Convert to absolute path.
base_dir="$(cd -- "$base_dir" && pwd -P;)"

# Check for the presence of the configuration file in the current directory.
config_file="$base_dir/app.cfg"
if [ ! -e "$config_file" ]
then
  echo "Error: No configuration file at $config_file."
  exit;
fi

# Generate a detached container from the local image.
# Mount the current directory to the usr/src/app/instance folder of the container, so that the
# application can find the configuration file on the host machine.
# Use port 5000.

echo "Starting application..."

docker run \
  -d \
  --rm \
  --name donor-metadata-local \
  -v "$base_dir":/usr/src/app/instance\
  -v "$base_dir/logs":/usr/src/app/neo4j/logs
  -p 5000:5000 hmsn/donor-metadata-local;

# Wait for the application to load completely.
# Extract the response code from a curl of the url and sleep until it is 200.
url="http://127.0.0.1:5000"
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
