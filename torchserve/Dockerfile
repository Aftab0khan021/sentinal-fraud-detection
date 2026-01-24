FROM pytorch/torchserve:latest

# Install additional dependencies
USER root
RUN pip install --no-cache-dir \
    torch-geometric \
    redis \
    prometheus-client

# Create directories
RUN mkdir -p /home/model-server/model-store
RUN mkdir -p /home/model-server/workflow-store
RUN mkdir -p /home/model-server/logs

# Copy configuration
COPY config.properties /home/model-server/config.properties

# Set permissions
RUN chown -R model-server:model-server /home/model-server

# Switch to model-server user
USER model-server

# Expose ports
# 8080: Inference API
# 8081: Management API  
# 8082: Metrics API
EXPOSE 8080 8081 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/ping || exit 1

# Start TorchServe
CMD ["torchserve", \
     "--start", \
     "--model-store", "/home/model-server/model-store", \
     "--workflow-store", "/home/model-server/workflow-store", \
     "--ts-config", "/home/model-server/config.properties"]
