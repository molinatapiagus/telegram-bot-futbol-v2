async def obtener_partidos_hoy():
    hoy = datetime.utcnow().strftime("%Y-%m-%d")

    # 1. Buscar partidos programados para hoy
    url_hoy = f"{API_BASE}/fixtures?date={hoy}"
    r1 = requests.get(url_hoy, headers=HEADERS)
    data1 = r1.json()

    partidos = data1.get("response", [])

    # 2. Si hoy no hay, buscar partidos EN VIVO
    if not partidos:
        url_live = f"{API_BASE}/fixtures?live=all"
        r2 = requests.get(url_live, headers=HEADERS)
        data2 = r2.json()
        partidos = data2.get("response", [])

    # 3. Si sigue vacío, buscar próximos
    if not partidos:
        url_next = f"{API_BASE}/fixtures?next=10"
        r3 = requests.get(url_next, headers=HEADERS)
        data3 = r3.json()
        partidos = data3.get("response", [])

    return partidos


