import logging
import asyncio
import aiohttp

from config import SERVERS, SLACK_WEBHOOK_URL

logger = logging.getLogger('server_pinger')

PING_FREQUENCY = 60
TIMEOUT = 10

OK_PREFIX = ':heavy_check_mark'
FAIL_PREFIX = ':heavy_multiplication_x:'


async def post_slack(session, message):
    await session.request('POST', url=SLACK_WEBHOOK_URL, json={'text': message})


async def get(url, session):
    url = url + '/robots.txt'
    return await session.request('GET', url=url, timeout=TIMEOUT)


async def ping_server(server, session):
    try:
        response = await get(server['url'], session)
        if response.status not in [200, 301, 302]:
            logger.error(f'{server["name"]} FAIL')
            if server['previous_status'] == 'OK':
                await post_slack(session, f'{FAIL_PREFIX} - {server["name"]} responded with HTTP{response.status}')
                server['previous_status'] = 'FAIL'
        else:
            logger.error(f'{server["name"]} OK')
            if server['previous_status'] == 'FAIL':
                await post_slack(session, f'{OK_PREFIX} - {server["name"]} is back up!')
                server['previous_status'] = 'OK'
    except asyncio.TimeoutError:
        logger.error(f'{server["name"]} TIMEOUT')
        if server['previous_status'] == 'OK':
            await post_slack(session, f'{FAIL_PREFIX} - {server["name"]} timed out after {TIMEOUT} seconds')
            server['previous_status'] = 'FAIL'
    except aiohttp.client_exceptions.ClientConnectorError:
        logger.error(f'{server["name"]} CONNECTION_ERROR')
    await asyncio.sleep(PING_FREQUENCY)


async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            logger.info('Pinging servers...')
            # Make a task for each server then await them all
            tasks = [ping_server(server, session) for server in SERVERS]
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
