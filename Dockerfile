FROM node:lts-slim

# Set working directory
WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies (including dev dependencies)
RUN npm install --include=dev

# Copy TypeScript configuration
COPY tsconfig.json ./

# Copy source files
COPY src/ ./src/

# Build the application
RUN npm run build

# Set Node to show more debug info
ENV NODE_DEBUG=*

# Start with debug info
CMD ["sh", "-c", "echo 'Token:' $GITHUB_PERSONAL_ACCESS_TOKEN && node --trace-warnings dist/index.js"]

# Expose the default port
EXPOSE 3000

# Set default environment variable for PORT
ENV PORT=3000

# Start the server
CMD ["node", "dist/index.js"] 