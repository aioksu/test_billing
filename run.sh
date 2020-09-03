docker-compose build --no-cache
docker-compose up -d db
docker-compose up -d rest
docker exec db bash -c "mysql -u root -ppassword -D billing < /tmp/initial.sql"

