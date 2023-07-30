import asyncio
import datetime
from sys import stderr
import os
from loguru import logger

from galxy import Galxy
from config import *


async def get_info(ID):
    info = await Galxy.get_info_by_id(ID)
    data = info['data']['campaign']

    status, number_id, name, chain = data['status'], \
        data['numberID'], \
        data['name'], \
        data['chain']


    return status, number_id, name, chain

def check_claim_data(claim_nft_data,INFO_NFT,ADDRESS):
    if claim_nft_data['data'].get('prepareParticipate').get('allow') ==False :
        if claim_nft_data['data'].get('prepareParticipate').get('disallowReason') == 'Exceed limit, available claim count is 0':
            logger.error(
                f"CLAIM | ERROR | {INFO_NFT[-2]} | {ADDRESS} | Claim is not available")
            return True
        logger.info(f"CLAIM | FAILED | {INFO_NFT[-2]} | {ADDRESS} | {claim_nft_data['data']['prepareParticipate']['disallowReason']}")
        return True
    return False


async def claimer(address,ID,INFO_NFT):
    claim_nft_data = await Galxy.claim(address,ID,W,INFO_NFT[-1])
    if check_claim_data(claim_nft_data,INFO_NFT,address):return

    if (claim_nft_data['data']['prepareParticipate']['loyaltyPointsTxResp']):
        logger.info(f'CLAIM | SUCCESS | {INFO_NFT[-2]} | {address}')
    else:
        logger.info(f'CLAIM | FAILED | {INFO_NFT[-2]} | {address}')


async def claim_nft_queue(queue: asyncio.Queue):
    while not queue.empty():
        data_account = await queue.get()

        for camp_id in task_list:
            if len(camp_id) >10:
                camp_id = camp_id.split('/')[-1]

            information_by_id = await get_info(camp_id)
            
            if information_by_id[0] == 'Active':
                await claimer(data_account,camp_id,information_by_id)


async def work():
    queue_id = asyncio.Queue()

    for address in address_list:
        queue_id.put_nowait(address)

    claim_work = [claim_nft_queue(queue_id) for i in range(STREAMS)]
    await asyncio.gather(*claim_work)

# ***********************************************************************************************************

logger.remove()
logger.add(stderr,
           format="<white>{time:HH:mm:ss}</white> | "
                  "<level>{level: <2}</level> | "
                  "<white>{function}</white> | "
                  "<white>{line}</white> - "
                  "<white>{message}</white>")

date = datetime.datetime.now().utcnow().strftime("%H-%M-%S")
logger.add(f"./log/file_{date}.log")


address_path = os.path.abspath('data_file/address.txt')
with open(address_path, 'r') as f:
    address_list = [i for i in [i.strip() for i in f] if i != '']

task_path = os.path.abspath('data_file/task.txt')
with open(task_path, 'r') as f:
    task_list = [i for i in [i.strip() for i in f] if i != '']

# ***********************************************************************************************************   
    
    
async def main():
    assert len(address_list) > 0, 'Add addresses address.txt'
    assert len(task_list) > 0, 'Add campaign id task.txt | format galxe.com/perp/campaign/XXXXXX OR GCUEJK'

    if not await Galxy.validation_config_w(W):
        logger.info('Change W at config.py')
        return
    else:
        await work()

