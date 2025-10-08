import sys
# força MTA antes de qualquer import que manipule COM/WinRT
sys.coinit_flags = 0

import asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from bleak.backends.winrt.util import allow_sta
    allow_sta()
except Exception:
    pass

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import traceback

# Substring do nome do carrinho
TARGET_NAME_SUBSTRING = "SL-296"  # pode ser "SL-296 GT3" ou apenas "SL-296"

async def scan_and_list(timeout=8.0):
    print(f"Escaneando dispositivos BLE por {timeout} segundos...")
    devices = await BleakScanner.discover(timeout=timeout)
    if not devices:
        print("Nenhum dispositivo BLE encontrado.")
        return devices

    print(f"\n{len(devices)} dispositivos encontrados:")
    for i, d in enumerate(devices, 1):
        name = d.name or "<sem nome>"
        rssi = getattr(d, "rssi", "N/A")
        print(f"{i:02d}) {name}  —  {d.address}  (rssi: {rssi})")
    return devices

async def try_connect_and_dump(address):
    print(f"\nTentando conectar ao dispositivo {address} ...")
    try:
        async with BleakClient(address, timeout=10.0) as client:
            connected = client.is_connected  # propriedade, não coroutine
            print("Conectado?" , connected)
            if not connected:
                print("Não foi possível conectar.")
                return

            # Atualiza serviços (Bleak 2.6.1)
            if client.services is None:
                await client.get_services()
            services = client.services

            print("\nServiços e Characteristics:")
            for svc in services:
                print(f"\n[Service] {svc.uuid}: {svc.description}")
                for ch in svc.characteristics:
                    props = ",".join(ch.properties)
                    print(f"  - Characteristic {ch.uuid} | props: {props} | desc: {ch.description}")
                    # tenta ler se possível
                    if "read" in ch.properties:
                        try:
                            val = await client.read_gatt_char(ch.uuid)
                            hex_preview = val.hex()[:200]
                            print(f"      -> READ ({len(val)} bytes): {hex_preview}")
                        except Exception as e:
                            print(f"      -> READ falhou: {e}")
                    # descriptors
                    for des in ch.descriptors:
                        try:
                            dval = await client.read_gatt_descriptor(des.handle)
                            print(f"      Descriptor handle {des.handle}: {dval.hex()}")
                        except Exception:
                            pass

            print("\nFim do dump de serviços/characteristics.")
    except BleakError as be:
        print("BleakError ao conectar/operar:", be)
    except Exception as e:
        print("Erro inesperado:", e)
        traceback.print_exc()

async def main():
    devices = await scan_and_list(timeout=8.0)

    if not devices:
        print("\nSe você tem certeza que o carrinho está ligado e pareado ao PC, tente aumentar o timeout ou use o app nRF Connect no celular para verificar se ele anuncia serviços BLE.")
        return

    # procura pelo alvo pelo nome
    target = None
    for d in devices:
        if d.name and TARGET_NAME_SUBSTRING.lower() in d.name.lower():
            target = d
            break

    if target:
        print(f"\nDispositivo alvo encontrado: {target.name} — {target.address}")
        await try_connect_and_dump(target.address)
    else:
        print(f"\nNenhum dispositivo com '{TARGET_NAME_SUBSTRING}' no nome foi encontrado.")
        print("Lista completa acima — localize o seu dispositivo e copie o address (ex: XX:XX:XX:XX:XX:XX).")

if __name__ == "__main__":
    asyncio.run(main())
