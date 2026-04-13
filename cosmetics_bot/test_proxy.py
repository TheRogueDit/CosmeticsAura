import asyncio
from aiohttp_socks import ProxyConnector
import aiohttp

async def test():
    proxies = [
        "socks5://185.162.230.55:4145",
        "socks5://91.107.234.133:1080",
    ]
    
    for proxy in proxies:
        try:
            connector = ProxyConnector.from_url(proxy)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("https://api.telegram.org", timeout=10) as r:
                    print(f"✅ {proxy} — работает!")
                    return
        except:
            print(f"❌ {proxy} — не работает")
    
    print("❌ Ни один прокси не подошёл")

asyncio.run(test())
