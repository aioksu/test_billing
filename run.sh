docker-compose build --no-cache
docker-compose up -d
docker exec db bash -c "mysql -u root -ppassword -D billing < /tmp/initial.sql"

