FROM cardiff-racing:base

# Copy test data
COPY test_data/ /workspace/test_data/

# Set working directory
WORKDIR /workspace

# Default command
CMD ["bash"]