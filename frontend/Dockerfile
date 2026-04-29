FROM node:20-alpine

WORKDIR /app

COPY package.json tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY src ./src

RUN npm install
RUN npm run build

EXPOSE 4173

CMD ["npm", "run", "preview"]
