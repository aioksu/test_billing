# test_billing

# How to start

Use run.sh to start app

# How to use

> Create customer

curl -X POST "http://127.0.0.1:8080/customer"

> Add money to wallet

curl -X POST "http://127.0.0.1:8080/add_money?wallet_id=1&money=1"

> Transfer money from one to another wallet

curl -X POST "http://127.0.0.1:8080/transfer_money?sender=1&recipient=2&money=1"

sender - customer's wallet id who would send money

recipient - customer's wallet id whom would send money

