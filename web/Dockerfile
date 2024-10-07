# Use an official Node.js image as the base image
FROM node:14

# Install Python, pip, and Rust
RUN apt-get update && apt-get install -y python3 python3-pip curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    /root/.cargo/bin/rustc --version && \
    echo 'export PATH=$HOME/.cargo/bin:$PATH' >> /root/.bashrc

# Ensure Rust is available in the PATH for subsequent RUN commands
ENV PATH="/root/.cargo/bin:${PATH}"


# Install Python packages
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Create and change to the app directory
WORKDIR /usr/src/app

# Copy application dependency manifests to the container image.
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Install client dependencies
RUN npm install --prefix s8oa

# Install concurrently to run both server and client
RUN npm install -g concurrently

# Copy the rest of the application code to the container
COPY . .

# Build the React application
RUN npm run build --prefix s8oa

# Expose the ports the app runs on
EXPOSE 3000
EXPOSE 3001

# Start both server and React application
CMD ["concurrently", "\"node server.js\"", "\"npm start --prefix s8oa\""]
