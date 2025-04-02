FROM python:3.11-alpine

LABEL description="HuBMAP/SenNet Donor Clinical Metadata Curator service"

# Set up environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /usr/src/app

# Copy only the requirements file first to leverage Docker caching
COPY app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY app .

# Expose the port your application will run on
EXPOSE 7000

# Specify the command to run on container start
CMD ["python", "/usr/src/app/app.py"]