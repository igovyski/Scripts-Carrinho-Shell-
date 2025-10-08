import sys
import asyncio

sys.coinit_flags = 0

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from bleak.backends.winrt.util import allow_sta
    allow_sta()
except Exception:
    pass

import pygame
from bleak import BleakClient

CAR_ADDRESS = "13:05:AA:06:E4:62"
CONTROL_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# Botão que alterna a luz
LUZ_TOGGLE_BUTTON = 8

# Botões para movimento (mapeamento para cada byte do comando)
# chave: botão pygame, valor: índice do byte no comando (0-indexado)
BUTTON_MAPPING = {
    0: 0,  # frente
    1: 1,  # ré
    13: 2, # esquerda
    14: 3, # direita
    # O botão da luz não entra aqui porque é tratado separadamente
}

# Botão turbo (agora em modo toggle)
TURBO_BUTTON = 12

STOP_COMMAND = bytes.fromhex("ff00000000000000ff")

PREFIX = bytes.fromhex("ff")
SUFFIX = bytes.fromhex("ff")

async def ble_control_loop():
    print(f"Tentando conectar ao carro {CAR_ADDRESS} ...")
    async with BleakClient(CAR_ADDRESS) as client:
        if not client.is_connected:
            print("Não foi possível conectar ao carro!")
            return
        print("Conectado ao carro!")

        # Envia parada inicial
        try:
            print("Enviando comando de parada inicial...")
            await client.write_gatt_char(CONTROL_CHAR_UUID, STOP_COMMAND, response=False)
        except Exception as e:
            print(f"Erro ao enviar comando de parada inicial: {e}")

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("Nenhum joystick detectado! Conecte o controle e tente novamente.")
            return

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Joystick detectado: {joystick.get_name()}")

        pressed_buttons = set()
        last_command_sent = None
        luz_ligada = False
        turbo_ligado = False
        running = True
        clock = pygame.time.Clock()

        def montar_comando(pressed, luz, turbo):
            """
            Monta o comando com 6 bytes:
            0: frente
            1: ré
            2: esquerda
            3: direita
            4: luz
            5: turbo
            """
            bytes_comando = [0] * 6  # inicializa tudo desligado

            # Preenche os motores
            for btn in pressed:
                if btn in BUTTON_MAPPING:
                    idx = BUTTON_MAPPING[btn]
                    bytes_comando[idx] = 1

            # Luz
            bytes_comando[4] = 1 if luz else 0

            # Turbo
            bytes_comando[5] = 1 if turbo else 0

            comando = PREFIX + bytes(bytes_comando) + SUFFIX
            return comando

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

                elif event.type == pygame.JOYBUTTONDOWN:
                    btn = event.button

                    if btn == LUZ_TOGGLE_BUTTON:
                        luz_ligada = not luz_ligada
                        print(f"Luz {'ligada' if luz_ligada else 'desligada'}")
                        continue
                    elif btn == TURBO_BUTTON:
                        turbo_ligado = not turbo_ligado
                        print(f"Turbo {'ligado' if turbo_ligado else 'desligado'}")
                        continue

                    pressed_buttons.add(btn)

                elif event.type == pygame.JOYBUTTONUP:
                    btn = event.button
                    # Remover botão solto da lista de pressionados
                    pressed_buttons.discard(btn)

                # Monta e envia comando
                current_command = montar_comando(pressed_buttons, luz_ligada, turbo_ligado)

                if current_command != last_command_sent:
                    print(f"Enviando comando: {current_command.hex()}")
                    try:
                        await client.write_gatt_char(CONTROL_CHAR_UUID, current_command, response=False)
                        last_command_sent = current_command
                    except Exception as e:
                        print(f"Erro ao enviar comando: {e}")

            clock.tick(30)

        print("Encerrando controle...")
        pygame.quit()

async def main():
    await ble_control_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Programa encerrado pelo usuário")
