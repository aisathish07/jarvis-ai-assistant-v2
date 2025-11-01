import time, asyncio, aiohttp, statistics as st
url = "https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current_weather=true"
async def lat():
    t0 = time.perf_counter()
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r: await r.text()
    return (time.perf_counter() - t0) * 1000
times = [asyncio.run(lat()) for _ in range(50)]
print("Median latency:", st.median(times), "ms")