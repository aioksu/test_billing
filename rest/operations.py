import aiomysql
from datetime import datetime as dt
from decimal import Decimal


import logging


logger = logging.getLogger()


async def add_money_to_wallet(conn, session_id, wallet_id, money):
    logger.info(
        f'[{session_id}] Start add money {money} to wallet id {wallet_id}')

    async with conn.cursor() as cursor:
        try:
            await conn.begin()
            await cursor.execute('SELECT balance FROM wallet WHERE id = %s FOR UPDATE', (wallet_id))
            balance = await cursor.fetchone()

            if balance is None:
                await conn.commit()
                return {
                    'error': f'wallet_id {wallet_id} not found'
                }

            balance = balance[0]
            balance += Decimal(money)

            await cursor.execute('UPDATE wallet SET balance = %s WHERE id = %s', (balance, wallet_id))

            await conn.commit()

            return {
                'data': {
                    'balance': balance}
            }

        except Exception as e:
            await conn.rollback()
            await conn.commit()

            logger.exception(f'[{session_id}] Add money to wallet {e}')
            return {
                'error': f'Error adding money to wallet: {e}'
            }


async def transfer_money_from_wallet_to_wallet(conn, session_id, sender_wallet_id, recipient_wallet_id, money):

    async with conn.cursor(aiomysql.cursors.DictCursor) as cursor:
        try:
            await conn.begin()

            await cursor.execute('SELECT * FROM wallet '
                                 'WHERE id in (%s, %s) FOR UPDATE',
                                 (sender_wallet_id, recipient_wallet_id))

            wallets = await cursor.fetchall()

            if len(wallets) < 2:
                return {
                    'error': f'wrong wallet_id'
                }

            sender_balance = wallets[0]['balance'] if sender_wallet_id == wallets[0]['id'] \
                else wallets[1]['balance']

            recipient_balance = wallets[0]['balance'] if recipient_wallet_id == wallets[0]['id'] \
                else wallets[1]['balance']

            sender_new_balance = sender_balance - money

            if sender_new_balance < 0:
                await conn.commit()
                return {
                    'error': f'insufficient funds wallet_id {sender_wallet_id}'
                }

            recipient_balance = recipient_balance + money

            data_to_update = [
                (sender_wallet_id, sender_new_balance, str(dt.now())),
                (recipient_wallet_id, recipient_balance, str(dt.now())),
            ]

            await cursor.executemany('INSERT INTO wallet (id, balance, creation_time) VALUES (%s, %s, %s) '
                                     'ON DUPLICATE KEY UPDATE balance = VALUES(balance)',
                                     data_to_update)

            await conn.commit()

            return {
                'data':
                {
                    'sender': {
                        'wallet_id': sender_wallet_id,
                        'balance': sender_new_balance
                    },
                    'recipient': {
                        'wallet_id': recipient_wallet_id,
                        'balance': recipient_balance
                    }
                }
            }

        except Exception as e:
            await conn.rollback()
            await conn.commit()

            logger.exception(f'Add money to wallet {e}')
            return {
                'error': f'general error: {e}'
            }
