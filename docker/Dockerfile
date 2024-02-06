# What works: VallE
# This is an auto generated Dockerfile for ros:ros-core
# generated from docker_images/create_ros_core_image.Dockerfile.em
FROM ubuntu:focal

# Set the working directory
WORKDIR /app

# setup timezone
RUN echo 'Etc/UTC' > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && \
    apt-get install -q -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

# install packages
RUN apt-get update && apt-get install -q -y --no-install-recommends \
    dirmngr \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# setup keys
RUN set -eux; \
    key='C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654'; \
    export GNUPGHOME="$(mktemp -d)"; \
    gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "$key"; \
    mkdir -p /usr/share/keyrings; \
    gpg --batch --export "$key" > /usr/share/keyrings/ros1-latest-archive-keyring.gpg; \
    gpgconf --kill all; \
    rm -rf "$GNUPGHOME"

# setup sources.list
RUN echo "deb [ signed-by=/usr/share/keyrings/ros1-latest-archive-keyring.gpg ] http://packages.ros.org/ros/ubuntu focal main" > /etc/apt/sources.list.d/ros1-latest.list

# setup environment
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ENV ROS_DISTRO noetic

# install ros packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-ros-core=1.5.0-1* \
    && rm -rf /var/lib/apt/lists/*
# setup entrypoint
COPY ./docker/ros_entrypoint.sh /

CMD ["bash"]

# Copy requirements.txt into the container
COPY ./docker/packages-python3.txt .
COPY ./docker/packages-apt.txt .

# Install any additional system packages needed
RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && xargs -a packages-apt.txt apt-get install -y

# Install any additional Python packages needed
RUN apt-get update && apt-get install python3 -y
RUN echo "alias python=python3" >> /root/.bashrc
RUN apt-get update && apt-get install -y python3-pip

# CUDA compiler
RUN apt clean
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
RUN mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
RUN wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-ubuntu2004-12-1-local_12.1.0-530.30.02-1_amd64.deb
RUN dpkg -i cuda-repo-ubuntu2004-12-1-local_12.1.0-530.30.02-1_amd64.deb
RUN cp /var/cuda-repo-ubuntu2004-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
RUN apt-get update
RUN apt-get -y install cuda

RUN pip3 install torch torchvision torchaudio
RUN pip install --no-cache-dir -r packages-python3.txt

# Copy the rest of the application code into the container
COPY . .


RUN pip install --upgrade openai alive-progress scikit-learn tqdm openai-whisper ffmpeg-python setuptools-rust
ENV export OPENAI_API_KEY="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"
RUN echo "alias python=python3" >> /root/.bashrc
RUN chmod 755 /app/docker/entrypoint.sh

RUN apt-get install libportaudio2

ENTRYPOINT ["bash",  "/app/docker/entrypoint.sh" ]