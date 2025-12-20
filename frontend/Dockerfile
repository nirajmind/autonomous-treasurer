# Stage 1: Build the Vue application
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
# (Optional) Add custom nginx config here if needed for API proxying
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]