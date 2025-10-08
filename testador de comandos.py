import asyncio
import struct
from bleak import BleakClient, BleakScanner

# UUIDs do seu dispositivo
DEVICE_NAME = "SL-296 GT3"
DEVICE_ADDRESS = "13:05:AA:06:E4:62"

# UUIDs dos serviços e characteristics
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"  # Para enviar comandos
NOTIFY_CHAR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"  # Para receber notificações

# Comandos básicos para testar (ajuste conforme necessário)
COMANDOS_TESTE = {
    "frente": [
        b'\x01', b'\x02', b'\x03', b'\x04', b'\x05',
        b'\xff\x01\x01\x64\xff',  # Padrão comum
        b'\x07\x00\x01\x64\x00',  # Outro padrão
        b'\x01\x64', b'\x02\x64',
        b'\x46\x57\x0d\x0a',  # FW + CRLF (comum em alguns controles)
        b'\x46\x57'  # FW
    ],
    "ré": [
        b'\x06', b'\x07', b'\x08', b'\x09', b'\x0a',
        b'\xff\x01\x02\x64\xff',
        b'\x07\x00\x02\x64\x00',
        b'\x06\x64', b'\x07\x64',
        b'\x42\x57\x0d\x0a',  # BW + CRLF
        b'\x42\x57'  # BW
    ],
    "esquerda": [
        b'\x0b', b'\x0c', b'\x0d', b'\x0e',
        b'\xff\x01\x03\x64\xff',
        b'\x07\x00\x03\x64\x00',
        b'\x0b\x64', b'\x0c\x64',
        b'\x4c\x45\x0d\x0a',  # LE + CRLF
        b'\x4c\x45'  # LE
    ],
    "direita": [
        b'\x0f', b'\x10', b'\x11', b'\x12',
        b'\xff\x01\x04\x64\xff',
        b'\x07\x00\x04\x64\x00',
        b'\x0f\x64', b'\x10\x64',
        b'\x52\x49\x0d\x0a',  # RI + CRLF
        b'\x52\x49'  # RI
    ],
    "parar": [
        b'\x00', b'\x13', b'\x14', b'\x15',
        b'\xff\x01\x00\x00\xff',
        b'\x07\x00\x00\x00\x00',
        b'\x53\x54\x0d\x0a',  # ST + CRLF
        b'\x53\x54'  # ST
    ],
    "luzes": [
        b'\x16', b'\x17', b'\x18',
        b'\xff\x01\x05\x00\xff',  # Comando para luzes
        b'\x4c\x49\x0d\x0a',  # LI + CRLF
        b'\x4c\x49'  # LI
    ]
}

def notification_handler(sender, data):
    """Função para lidar com notificações recebidas"""
    print(f"📨 Notificação recebida: {data.hex()} | Raw: {data}")

async def test_comandos():
    print(f"🔍 Procurando dispositivo {DEVICE_NAME}...")
    
    # Encontrar dispositivo
    devices = await BleakScanner.discover()
    target_device = None
    
    for device in devices:
        if device.name == DEVICE_NAME or device.address == DEVICE_ADDRESS:
            target_device = device
            break
    
    if not target_device:
        print("❌ Dispositivo não encontrado!")
        return
    
    print(f"✅ Dispositivo encontrado: {target_device.name} - {target_device.address}")
    
    async with BleakClient(target_device) as client:
        print(f"🔗 Conectado: {client.is_connected}")
        
        # ✅ CORREÇÃO: Use client.services em vez de client.get_services()
        services = client.services
        print("\n📋 Serviços disponíveis:")
        for service in services:
            print(f"  {service.uuid} - {service.description}")
            for char in service.characteristics:
                print(f"    {char.uuid} - {char.properties}")
        
        # Ativar notificações
        try:
            await client.start_notify(NOTIFY_CHAR_UUID, notification_handler)
            print("🔔 Notificações ativadas")
        except Exception as e:
            print(f"⚠️  Não foi possível ativar notificações: {e}")
        
        # Testar comandos
        print("\n🎮 Iniciando teste de comandos...")
        print("💡 DICA: Observe o carrinho e anote os comandos que funcionam!")
        
        comandos_que_funcionaram = []
        
        for movimento, comandos_list in COMANDOS_TESTE.items():
            print(f"\n🎯 Testando {movimento.upper()}:")
            
            for i, comando in enumerate(comandos_list, 1):
                try:
                    print(f"  Teste {i}: Enviando {comando.hex()}")
                    
                    # Enviar comando
                    await client.write_gatt_char(WRITE_CHAR_UUID, comando)
                    
                    # Aguardar um pouco para ver resposta
                    await asyncio.sleep(1.0)  # Aumentei o tempo para observar melhor
                    
                    # Parar entre comandos (safety)
                    parar_comando = b'\x00'
                    await client.write_gatt_char(WRITE_CHAR_UUID, parar_comando)
                    await asyncio.sleep(0.5)
                    
                    # Perguntar se funcionou
                    resposta = input("  ✅ Funcionou? (s/n): ").strip().lower()
                    if resposta == 's':
                        comandos_que_funcionaram.append((movimento, comando.hex()))
                        print(f"  🎉 COMANDO FUNCIONOU: {movimento} - {comando.hex()}")
                    
                except Exception as e:
                    print(f"  ❌ Erro ao enviar comando: {e}")
        
        # Parar notificações
        await client.stop_notify(NOTIFY_CHAR_UUID)
        
        # Mostrar resumo
        print("\n" + "="*50)
        print("📊 RESUMO DOS COMANDOS QUE FUNCIONARAM:")
        print("="*50)
        if comandos_que_funcionaram:
            for movimento, comando in comandos_que_funcionaram:
                print(f"🎯 {movimento.upper()}: {comando}")
        else:
            print("❌ Nenhum comando funcionou. Tente o modo interativo.")
        print("="*50)

async def comando_interativo():
    """Modo interativo para testar comandos específicos"""
    print("🎮 Modo Interativo - Digite comandos em hex (ex: FF0164FF) ou 'quit' para sair")
    
    async with BleakClient(DEVICE_ADDRESS) as client:
        try:
            await client.start_notify(NOTIFY_CHAR_UUID, notification_handler)
            print("🔔 Notificações ativadas")
        except Exception as e:
            print(f"⚠️  Não foi possível ativar notificações: {e}")
        
        while True:
            try:
                user_input = input("\n🔧 Comando hex: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    break
                elif user_input.lower() == 'help':
                    print("\n📝 Comandos especiais:")
                    print("  quit, exit, sair - Sair do modo interativo")
                    print("  help - Mostrar esta ajuda")
                    print("  stop, parar - Enviar comando de parada (00)")
                    print("  list - Listar comandos de teste")
                    continue
                elif user_input.lower() in ['stop', 'parar']:
                    user_input = '00'
                elif user_input.lower() == 'list':
                    print("\n📋 Comandos de teste sugeridos:")
                    for movimento, comandos in COMANDOS_TESTE.items():
                        print(f"  {movimento}: {comandos[0].hex()} (primeiro da lista)")
                    continue
                
                if user_input:
                    # Converter string hex para bytes
                    comando_bytes = bytes.fromhex(user_input.replace(' ', ''))
                    print(f"📤 Enviando: {comando_bytes.hex()}")
                    
                    await client.write_gatt_char(WRITE_CHAR_UUID, comando_bytes)
                    
                    # Pequena pausa
                    await asyncio.sleep(0.1)
                    
            except ValueError as e:
                print(f"❌ Formato inválido! Use hex (ex: FF0164FF). Erro: {e}")
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        try:
            await client.stop_notify(NOTIFY_CHAR_UUID)
        except:
            pass

async def descobrir_dispositivos():
    """Função para descobrir dispositivos BLE próximos"""
    print("🔍 Procurando dispositivos BLE...")
    devices = await BleakScanner.discover()
    
    print("\n📱 Dispositivos encontrados:")
    for i, device in enumerate(devices, 1):
        print(f"{i:2d}) {device.name or 'Sem nome'} - {device.address} (RSSI: {device.rssi})")
    
    return devices

# Menu principal
async def main():
    print("=" * 50)
    print("🚗 CONTROLADOR SL-296 GT3")
    print("=" * 50)
    
    while True:
        print("\nOpções:")
        print("1 - Teste automático de comandos")
        print("2 - Modo interativo") 
        print("3 - Descobrir dispositivos BLE")
        print("4 - Sair")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "1":
            await test_comandos()
        elif escolha == "2":
            await comando_interativo()
        elif escolha == "3":
            await descobrir_dispositivos()
        elif escolha == "4":
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    # Instalar dependência: pip install bleak
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Programa interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")