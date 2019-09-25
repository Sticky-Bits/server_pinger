import logging
import asyncio
import aiohttp

from db import get_slack_url, get_servers, set_server_status

logger = logging.getLogger('server_pinger')
logging.basicConfig(
    level=logging.INFO,
    filename='pingping.log',
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s',
)

TIMEOUT = 10

OK_PREFIX = ':heavy_check_mark:'
FAIL_PREFIX = ':heavy_multiplication_x:'

SLACK_WEBHOOK_URL = get_slack_url()
SERVERS = get_servers()


async def post_slack(session, message):
    await session.request('POST', url=SLACK_WEBHOOK_URL, json={'text': message})


async def get(url, session):
    url = url + '/robots.txt'
    return await session.request('GET', url=url, timeout=TIMEOUT)


async def ping_server(server, session):
    name, url, previous_status = server
    try:
        response = await get(url, session)
        if response.status not in [200, 301, 302]:
            logger.info(f'{name} FAIL')
            if previous_status == 'OK':
                await post_slack(session, f'{FAIL_PREFIX} - {name} responded with HTTP{response.status}')
                set_server_status(name, 'FAIL')
        else:
            logger.info(f'{name} OK')
            if previous_status == 'FAIL':
                await post_slack(session, f'{OK_PREFIX} - {name} is back up!')
                set_server_status(name, 'OK')
    except asyncio.TimeoutError:
        logger.info(f'{name} TIMEOUT')
        if previous_status == 'OK':
            await post_slack(session, f'{FAIL_PREFIX} - {name} timed out after {TIMEOUT} seconds')
            set_server_status(name, 'FAIL')
    except aiohttp.client_exceptions.ClientConnectorError:
        logger.info(f'{name} CONNECTION_ERROR')


async def main():
    async with aiohttp.ClientSession() as session:
        logger.info('Pinging servers...')
        # Make a task for each server then await them all
        tasks = [ping_server(server, session) for server in SERVERS]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
