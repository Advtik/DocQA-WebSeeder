# 1. Base image
FROM node:20-alpine

# 2. Set working directory
WORKDIR /app

# 3. Copy package files
COPY package.json package-lock.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy rest of code
COPY . .

# 6. Expose port
EXPOSE 5173

# 7. Start dev server
CMD ["npm", "run", "dev", "--", "--host"]