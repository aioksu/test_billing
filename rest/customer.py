from datetime import datetime as dt

import logging

logger = logging.getLogger()


async def create_customer(conn, session_id):
    logger.info('Start create new customer')

    async with conn.cursor() as cursor:
        try:
            await conn.begin()

            await cursor.execute("INSERT INTO wallet (balance, creation_time) VALUES (%s, %s)", (0, str(dt.now())))
            wallet_id = conn.insert_id()

            await cursor.execute("INSERT INTO customer (wallet_id, creation_time) VALUES (%s, %s)", (wallet_id, str(dt.now())))
            customer_id = conn.insert_id()

            await conn.commit()

            logger.info(
                f'[{session_id}] New customer with customer_id {customer_id} was successfully created')
            return {
                'data': {
                    'customer_id': customer_id,
                    'wallet_id': wallet_id
                }}
        except Exception as e:
            await conn.rollback()
            await conn.commit()

            logger.error(
                f'[{session_id}] Creating new customer was failed: {e}')
            return {'error': f'Cant create new customer: {e}'}
