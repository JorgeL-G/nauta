import asyncio
import random
import string
from datetime import datetime, timedelta, timezone, date

import httpx

# =========================
# Configuración
# =========================
ENDPOINT = "http://0.0.0.0:8000/transactions/"
TOTAL_REQUESTS = 1000000
CONCURRENCY = 50          # Ajusta si tu API es sensible a carga
TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 3           # Reintentos por request (429/5xx/errores de red)
RETRY_BASE_DELAY = 0.25   # segundos (exponencial: 0.25, 0.5, 1.0, ...)

CURRENCIES = ["USD","EUR","MXN","GBP","JPY","CAD","AUD","CHF","CNY","BRL"]
CATEGORIES = [
    "ALIMENTOS","ENTRETENIMIENTO","SALUD","TRANSPORTE","EDUCACION",
    "VIVIENDA","SERVICIOS","IMPUESTOS","SEGUROS","VIAJES",
    "TECNOLOGIA","HOGAR","ROPA","CALZADO","DEPORTES",
    "OCIO","RESTAURANTES","SUPERMERCADO","FARMACIA","MASCOTAS",
    "REGALOS","DONACIONES","SUSCRIPCIONES","GASOLINA","MANTENIMIENTO",
    "TELECOM","BANCA","OTROS","HARDWARE","SOFTWARE"
]

# =========================
# Generadores de datos
# =========================
def rand_amount(min_v=0.01, max_v=10000.0) -> float:
    return round(random.uniform(min_v, max_v), 2)

def rand_currency() -> str:
    return random.choice(CURRENCIES)

def rand_past_iso() -> str:
    """
    Fecha en los últimos 3 años hasta ahora (no futura),
    en formato ISO 8601 (YYYY-MM-DD) solo fecha, sin hora.
    """
    today = date.today()
    three_years = 365 * 3
    days_back = random.randint(0, three_years)
    d = today - timedelta(days=days_back)
    return d.isoformat()

def rand_category() -> str:
    # Si quieres categorías completamente libres, reemplaza por algo más aleatorio.
    return random.choice(CATEGORIES)

def make_payload() -> dict:
    return {
        "amount": rand_amount(),
        "currency": rand_currency(),
        "transaction_date": rand_past_iso(),
        "category": rand_category(),
    }

# =========================
# Lógica de envío
# =========================
async def post_with_retries(client: httpx.AsyncClient, json_body: dict) -> tuple[bool, int]:
    """
    Envía un POST con reintentos exponenciales ante 429/5xx o errores de red.
    Devuelve (exito: bool, status_code: int|0)
    """
    delay = RETRY_BASE_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await client.post(ENDPOINT, json=json_body)
            # Considera éxito cualquier 2xx
            if 200 <= resp.status_code < 300:
                return True, resp.status_code
            # Si es 429 o 5xx -> intentar reintento
            if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                return False, resp.status_code
            # Otras respuestas (4xx/3xx) se consideran fallo sin reintento
            return False, resp.status_code
        except (httpx.HTTPError, httpx.ReadTimeout, httpx.ConnectTimeout):
            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            return False, 0  # 0 = fallo de red sin status code

async def worker(name: int, queue: asyncio.Queue, client: httpx.AsyncClient, counters: dict):
    while True:
        i = await queue.get()
        if i is None:  # Sentinel para terminar
            queue.task_done()
            break
        payload = make_payload()
        ok, status = await post_with_retries(client, payload)
        if ok:
            counters["ok"] += 1
        else:
            counters["fail"] += 1
            counters["status_counts"][status] = counters["status_counts"].get(status, 0) + 1

        # Log liviano cada cierto número
        if i % 250 == 0:
            print(f"[Progreso] {i}/{TOTAL_REQUESTS} enviados | OK={counters['ok']} FAIL={counters['fail']}")
        queue.task_done()

async def main():
    # Cola de trabajos
    queue: asyncio.Queue = asyncio.Queue()
    for i in range(1, TOTAL_REQUESTS + 1):
        await queue.put(i)

    # Sentinels para cerrar workers al final
    for _ in range(CONCURRENCY):
        await queue.put(None)

    # Métricas
    counters = {"ok": 0, "fail": 0, "status_counts": {}}

    # Cliente HTTP
    limits = httpx.Limits(max_keepalive_connections=CONCURRENCY, max_connections=CONCURRENCY)
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        # Lanzar workers
        tasks = [
            asyncio.create_task(worker(i, queue, client, counters))
            for i in range(CONCURRENCY)
        ]
        # Esperar a que procesen la cola
        await queue.join()
        # Cancelar tareas (ya consumieron sentinel)
        for t in tasks:
            await t

    # Resumen
    print("\n================== RESUMEN ==================")
    print(f"Total intentos: {TOTAL_REQUESTS}")
    print(f"OK:   {counters['ok']}")
    print(f"FAIL: {counters['fail']}")
    if counters["status_counts"]:
        print("Códigos de respuesta en fallos:")
        for code, cnt in sorted(counters["status_counts"].items(), key=lambda x: x[0]):
            label = "ERROR_RED" if code == 0 else str(code)
            print(f"  {label}: {cnt}")

if __name__ == "__main__":
    asyncio.run(main())