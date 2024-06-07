# Building the docker images

cd api-gateway-service

docker build -t api-gateway-service .

cd ..

cd recognition-service
docker build -t recognition-service .
