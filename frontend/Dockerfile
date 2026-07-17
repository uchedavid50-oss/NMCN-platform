FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# NEXT_PUBLIC_* variables are inlined into the client JS bundle at BUILD time,
# not read at runtime — so this has to be a build ARG, not just a runtime env
# var. Railway automatically passes configured service variables as build args
# for Dockerfile builds, so setting NEXT_PUBLIC_API_URL in the Railway frontend
# service's variables is enough; nothing extra to configure on Railway's side.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000
CMD ["sh", "-c", "npm start -- -p ${PORT:-3000}"]
