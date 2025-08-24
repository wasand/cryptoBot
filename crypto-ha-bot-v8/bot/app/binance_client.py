from binance.spot import Spot as SpotClient
from .config import settings

def get_client():
    return SpotClient(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET,
        base_url='https://testnet.binance.vision' if settings.BINANCE_TESTNET else 'https://api.binance.com'
    )
