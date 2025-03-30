FROM nginx:alpine

# Copy the frontend files directly to nginx's serve directory
COPY frontend/ /usr/share/nginx/html/

# Copy nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 