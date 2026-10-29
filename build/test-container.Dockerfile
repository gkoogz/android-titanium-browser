FROM ubuntu:24.04
ARG BUILD_UID=1000
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates git python3 sudo curl xz-utils file lsb-release \
    && if ! getent passwd "${BUILD_UID}" >/dev/null; then \
         useradd --uid "${BUILD_UID}" --create-home --shell /bin/bash titanium; \
       fi \
    && printf 'ALL ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/titanium-build \
    && chmod 0440 /etc/sudoers.d/titanium-build \
    && rm -rf /var/lib/apt/lists/*
USER ${BUILD_UID}
ENV HOME=/build/home
ENV XDG_CACHE_HOME=/build/home/.cache
ENV CIPD_CACHE_DIR=/build/home/.cache/cipd
WORKDIR /input
CMD ["bash", "tools/build-test-apk.sh", "/build"]
