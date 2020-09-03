import aiomysql
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

    async with conn.cursor() as cursor:
        try:
            await conn.begin()

            await cursor.execute('SELECT balance FROM wallet '
                                 'WHERE id = %s FOR UPDATE',
                                 (sender_wallet_id))

            sender_balance = await cursor.fetchone()

            await cursor.execute('SELECT balance FROM wallet '
                                 'WHERE id = %s FOR UPDATE',
                                 (recipient_wallet_id))

            recipient_balance = await cursor.fetchone()

            if sender_balance is None or recipient_balance is None:
                await conn.commit()

                return {
                    'error': f'wrong wallet_id'
                }

            sender_balance, recipient_balance = sender_balance[
                0], recipient_balance[0]

            sender_new_balance = sender_balance - money

            if sender_new_balance < 0:
                await conn.commit()
                return {
                    'error': f'insufficient funds wallet_id {sender_wallet_id}'
                }

            recipient_balance = recipient_balance + money

            data_to_update = [
                (sender_wallet_id, sender_new_balance,),
                (recipient_wallet_id, recipient_balance,),
            ]

            await cursor.executemany('INSERT wallet (id, balance) VALUES (%s, %s) '
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
