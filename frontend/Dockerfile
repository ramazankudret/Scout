FROM node:20-slim

WORKDIR /app

# Install dependencies first (caching)
COPY package.json ./
RUN npm install --legacy-peer-deps

# Copy source
COPY . .

# Start development server
CMD ["npm", "run", "dev"]

