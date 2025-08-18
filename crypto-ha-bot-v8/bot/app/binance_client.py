from binance.spot import Spot as SpotClient
from .config import settings

def get_client():
    if settings.BINANCE_TESTNET:
        return SpotClient(key=settings.BINANCE_API_KEY, secret=settings.BINANCE_API_SECRET, base_url='https://testnet.binance.vision')
    return SpotClient(key=settings.BINANCE_API_KEY, secret=settings.BINANCE_API_SECRET)