from datetime import datetime as dt
import logging


logger = logging.getLogger()


async def set_log(conn, wallet_id=None, operation_time=None, current_balance=None,
                  add_funds=0, to_customer=None,
                  from_customer=None, status='pending',
                  *, operation, session_id):
    if not operation_time:
        operation_time = str(dt.now())

    async with conn.cursor() as cursor:
        try:
            await cursor.execute('INSERT INTO logs (operation_time, current_balance, add_funds,'
                                 'to_customer, from_customer, status,'
                                 'wallet_id, operation, session_id)'
                                 'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                                 (operation_time, current_balance, add_funds, to_customer,
                                  from_customer, status, wallet_id, operation, session_id))
        except Exception as e:
            logger.exception(f'Failed write to log: {e}')
            await conn.rollback()

            raise Exception('Failed write to log')
