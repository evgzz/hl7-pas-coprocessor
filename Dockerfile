# 1. Use an official, secure OpenJDK base image to handle the HL7 Validator JRE requirements

FROM eclipse-temurin:17-jre AS runtime-engine
# 2. Inject Python 3 into the core execution runtime container
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Establish our internal deployment execution paths
WORKDIR /app

# 4. Copy and lock down production python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. Populate the active operational code tree
COPY src/ ./src/
COPY fixtures/ ./fixtures/
# COPY ui_data/ ./ui_data/
COPY index.html .

# 6. Mirror the local binary payload structures internally
# COPY bin/ ./bin/

# 7. Pull the massive validation jar directly during cloud build if missing
RUN if [ ! -f bin/validator_cli.jar ]; then \
    curl -L -o bin/validator_cli.jar https://github.com/hapifhir/fhir-validator-app/releases/download/v6.1.3/validator_cli.jar; \
    fi

# 8. Expose the default network port used by your presentation dashboard
EXPOSE 8080

# 9. Launch the main orchestration pipeline process
CMD ["python3", "src/run_pipeline.py", "--host", "0.0.0.0", "--port", "8080"]
