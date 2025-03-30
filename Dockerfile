# Use an official Python runtime as a parent image
FROM python:3.9

# Install tzdata for timezone configuration and dependencies for Playwright
RUN apt-get update && apt-get install -y \
    tzdata \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libxfixes3 \
    libcups2 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libharfbuzz0b \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    libgdk-pixbuf2.0-0 \
    xdg-utils \
    wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the timezone to Europe/Riga (Latvia)
ENV TZ=Europe/Riga
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download and install Playwright browsers, including Chromium
RUN playwright install --with-deps chromium

# Ensure that no log files are created in the container (disable logging to files if possible)
RUN mkdir -p /app/logs && rm -rf /app/logs

# Optional: You can set the environment variable to disable file logging or manage it via your application config
ENV LOGGING_DISABLED=true

# Define the script execution as the container's entry point
ENTRYPOINT ["python", "-u", "main.py"]
