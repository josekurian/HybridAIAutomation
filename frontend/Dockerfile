FROM node:20-alpine

WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:5405
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY src ./src

RUN npm ci
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview"]
