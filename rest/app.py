
from aiohttp import web
from decimal import Decimal
import json
from functools import partial
from rest.utils import set_log
from rest.customer import create_customer
from rest.operations import add_money_to_wallet, transfer_money_from_wallet_to_wallet
import uuid
import os
import aiomysql
import logging


json_dumps = partial(json.dumps, default=lambda obj: str(
    obj) if isinstance(obj, Decimal) else obj)
json_response = partial(web.json_response, dumps=json_dumps)


logger = logging.getLogger()


def convert(convert_to_type, value):
    try:
        return convert_to_type(value)
    except Exception as e:
        logger.exception(f'Wrong data type {value}: {e}')


class RestEndpoint:

    def __init__(self):
        self.web_app = web.Application()
        self.web_app.add_routes(self.routes)

    @property
    def routes(self):
        return [
            web.post('/customer', self.add_customer),
            web.post('/add_money', self.add_money),
            web.post('/transfer_money', self.transfer_money),
        ]

    @staticmethod
    async def add_customer(request):
        session_id = str(uuid.uuid4())

        try:
            async with request.app['db'].acquire() as conn:
                await set_log(conn,
                              session_id=session_id,
                              operation='create_customer')

                result = await create_customer(conn, session_id)

                await set_log(conn,
                              wallet_id=result['data']['wallet_id'] if 'data' in result else None,
                              session_id=session_id,
                              current_balance=0,
                              operation='create_customer',
                              status='success' if 'data' in result else 'failed')
        except Exception as e:
            logger.exception(
                f'[{session_id}] Failed to process "add_customer": {e}')
            return web.HTTPInternalServerError()

        return json_response(result)

    @staticmethod
    async def add_money(request):
        session_id = str(uuid.uuid4())

        wallet_id = convert(int, request.query.get('wallet_id'))
        money = convert(Decimal, request.query.get('money'))

        try:
            async with request.app['db'].acquire() as conn:
                await set_log(conn,
                              wallet_id=wallet_id,
                              session_id=session_id,
                              add_funds=money,
                              operation='add_money')

                if wallet_id is None or money is None or money <= 0:
                    logger.error(
                        f'[{session_id}] Error add money to {wallet_id}')

                    await set_log(conn,
                                  wallet_id=wallet_id,
                                  session_id=session_id,
                                  add_funds=money,
                                  operation='add_money',
                                  status='failed')

                    return web.HTTPBadRequest()

                result = await add_money_to_wallet(conn, session_id, wallet_id, money)

                await set_log(conn,
                              wallet_id=wallet_id,
                              session_id=session_id,
                              operation='add_money',
                              current_balance=result['data']['balance']
                              if 'data' in result else None,
                              add_funds=money,
                              status='success' if 'data' in result else 'failed'
                              )
        except Exception as e:
            logger.exception(
                f'[{session_id}] Failed to process "add_money": {e}')
            return web.HTTPInternalServerError()

        return json_response(result)

    @staticmethod
    async def transfer_money(request):
        session_id = str(uuid.uuid4())

        sender_wallet_id = convert(int, request.query.get('sender'))
        recipient_wallet_id = convert(int, request.query.get('recipient'))
        money = convert(Decimal, request.query.get('money'))

        try:
            async with request.app['db'].acquire() as conn:
                await set_log(conn,
                              wallet_id=sender_wallet_id,
                              session_id=session_id,
                              add_funds=money,
                              operation='transfer_to',
                              to_customer=recipient_wallet_id)

                await set_log(conn,
                              wallet_id=recipient_wallet_id,
                              session_id=session_id,
                              add_funds=money,
                              operation='transfer_from',
                              from_customer=sender_wallet_id)

                if sender_wallet_id is None or recipient_wallet_id is None \
                        or money is None or money <= 0 \
                        or sender_wallet_id == recipient_wallet_id:

                    await set_log(conn,
                                  wallet_id=sender_wallet_id,
                                  session_id=session_id,
                                  add_funds=money,
                                  operation='transfer_to',
                                  to_customer=recipient_wallet_id,
                                  status='failed')

                    await set_log(conn,
                                  wallet_id=recipient_wallet_id,
                                  session_id=session_id,
                                  add_funds=money,
                                  operation='transfer_from',
                                  from_customer=sender_wallet_id,
                                  status='failed')

                    logger.error(
                        f'[{session_id}] Error transfer money from {sender_wallet_id} to {recipient_wallet_id}')

                    return web.HTTPBadRequest()

                result = await transfer_money_from_wallet_to_wallet(conn,
                                                                    session_id,
                                                                    sender_wallet_id,
                                                                    recipient_wallet_id,
                                                                    money)
                await set_log(conn,
                              wallet_id=sender_wallet_id,
                              session_id=session_id,
                              current_balance=result['data']['sender']['balance']
                              if 'data' in result else None,
                              add_funds=money,
                              operation='transfer_to',
                              to_customer=recipient_wallet_id,
                              status='success' if 'data' in result else 'failed')

                await set_log(conn,
                              wallet_id=recipient_wallet_id,
                              session_id=session_id,
                              current_balance=result['data']['recipient']['balance']
                              if 'data' in result else None,
                              add_funds=money,
                              operation='transfer_from',
                              from_customer=sender_wallet_id,
                              status='success' if 'data' in result else 'failed')
        except Exception as e:
            logger.exception(
                f'[{session_id}] Failed to process "transfer_money": {e}')
            return web.HTTPInternalServerError()

        return json_response(result)

    @staticmethod
    async def init_db(app):
        pool = await aiomysql.create_pool(
            host=os.environ['MYSQL_HOST'],
            port=int(os.environ['MYSQL_PORT']),
            user=os.environ['MYSQL_USER'],
            password=os.environ['MYSQL_PASSWORD'],
            db=os.environ['MYSQL_DB'],
            minsize=int(os.environ['MYSQL_MINSIZE']),
            maxsize=int(os.environ['MYSQL_MAXSIZE']),
            autocommit=True
        )
        app['db'] = pool

    @staticmethod
    async def close_db(app):
        app['db'].close()
        await app['db'].wait_closed()

    def start_endpoint(self):
        self.web_app.on_startup.append(self.init_db)
        self.web_app.on_cleanup.append(self.close_db)
        web.run_app(self.web_app)
