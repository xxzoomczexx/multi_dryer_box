#!/usr/bin/env python3
"""
Multi-box Filament Drybox - Serial to MQTT Bridge
=================================================
Tento skript cte telemetricka JSON data z USB CDC seriove linky Raspberry Pi Pico 2,
validuje jejich format a preposila je na zadany MQTT broker.

Zavislosti:
    pip install pyserial paho-mqtt

Pouziti:
    python serial_mqtt_bridge.py
    python serial_mqtt_bridge.py --port /dev/ttyACM0 --broker broker.hivemq.com --topic drybox/telemetry
"""

import sys
import time
import json
import argparse
import signal
from typing import Optional

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[CHYBA] Knihovna 'pyserial' neni nainstalovana. Spustte: pip install pyserial")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[CHYBA] Knihovna 'paho-mqtt' neni nainstalovana. Spustte: pip install paho-mqtt")
    sys.exit(1)


def find_default_serial_port() -> Optional[str]:
    """Pokusi se automaticky detekovat pripojene Raspberry Pi Pico."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None

    # Hledani podle Raspberry Pi USB VID/PID nebo popisu
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if "pico" in desc or "2e8a" in hwid or "ttyacm" in p.device.lower():
            return p.device

    # Fallback na prvni nalezeny port
    return ports[0].device


def validate_drybox_json(line: str) -> Optional[dict]:
    """
    Validuje prijaty retezec. Vraci slovnik dat nebo None pri chybe.
    Kontroluje pritomnost klicovych poli protokolu: id, weight, temp, hum, dry_state.
    """
    line = line.strip()
    if not (line.startswith("{") and line.endswith("}")):
        return None

    try:
        data = json.loads(line)
        required_keys = {"id", "weight", "temp", "hum", "dry_state"}
        if required_keys.issubset(data.keys()):
            return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Multi-box Filament Drybox - Serial to MQTT Gateway"
    )
    parser.add_argument(
        "--port",
        "-p",
        type=str,
        default=None,
        help="Seriovy port (napr. /dev/ttyACM0 nebo COM3). Pokud neni zadan, zkusi autodetekci.",
    )
    parser.add_argument(
        "--baud",
        "-b",
        type=int,
        default=115200,
        help="Baudrate seriove linky (vychozi: 115200)",
    )
    parser.add_argument(
        "--broker",
        type=str,
        default="broker.hivemq.com",
        help="Adresa MQTT brokeru (vychozi: broker.hivemq.com)",
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=1883,
        help="Port MQTT brokeru (vychozi: 1883)",
    )
    parser.add_argument(
        "--topic",
        "-t",
        type=str,
        default="drybox/status/1",
        help="MQTT topic pro publikaci (vychozi: drybox/status/1)",
    )

    args = parser.parse_args()

    # 1. Zjisteni serioveho portu
    port_name = args.port or find_default_serial_port()
    if not port_name:
        print("[CHYBA] Zadne seriove zarizeni nebylo nalezeno.")
        print("Pripojte Pico pres USB a zadejte port parametrem --port (napr. --port /dev/ttyACM0).")
        sys.exit(1)

    print("=" * 60)
    print("  MULTI-BOX FILAMENT DRYBOX - SERIAL -> MQTT GATEWAY")
    print("=" * 60)
    print(f"[*] Seriovy port : {port_name} @ {args.baud} baud")
    print(f"[*] MQTT Broker  : {args.broker}:{args.mqtt_port}")
    print(f"[*] MQTT Topic   : {args.topic}")
    print("=" * 60)

    # 2. Inicializace MQTT klienta (kompatibilni s paho-mqtt 1.x i 2.x)
    client_id = f"drybox_bridge_{int(time.time())}"
    try:
        # Paho MQTT 2.x API
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id
        )
    except AttributeError:
        # Paho MQTT 1.x API fallback
        client = mqtt.Client(client_id=client_id)

    ser = None
    connected_to_broker = False
    cmd_topic = "drybox/commands"

    def on_connect(c, userdata, flags, reason_code, properties=None):
        nonlocal connected_to_broker
        rc = getattr(reason_code, "value", reason_code)
        if rc == 0:
            connected_to_broker = True
            print(f"[MQTT] Uspesne pripojeno k brokeru '{args.broker}'.")
            c.subscribe(cmd_topic)
            print(f"[MQTT] Odebíram příkazy z topicu '{cmd_topic}'.")
        else:
            print(f"[MQTT] Chyba pripojeni k brokeru! Kod: {rc}")

    def on_message(c, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            print(f"[MQTT CMD] Přijat příkaz z webu: {payload}")
            if ser is not None and ser.is_open:
                ser.write(b"s")
        except Exception as e:
            print(f"[MQTT CMD] Chyba zpracování příkazu: {e}")

    def on_disconnect(c, userdata, *args):
        print("[MQTT] Odpojeno od brokeru.")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(f"[*] Pripojuji k MQTT brokeru '{args.broker}'...")
    try:
        client.connect(args.broker, args.mqtt_port, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"[CHYBA] Nelze se pripojit k MQTT brokeru: {e}")
        sys.exit(1)

    # Cekani na potvrzeni pripojeni
    timeout = time.time() + 5.0
    while not connected_to_broker and time.time() < timeout:
        time.sleep(0.1)

    # 3. Otevreni seriove linky
    print(f"[*] Oteviram seriovy port '{port_name}'...")
    try:
        ser = serial.Serial(port=port_name, baudrate=args.baud, timeout=1.0)
    except serial.SerialException as e:
        print(f"[CHYBA] Nelze otevrit seriovy port: {e}")
        client.loop_stop()
        client.disconnect()
        sys.exit(1)

    print("[*] Linka aktivni. Cekam na telemetrii ze zarizeni (Ukonceni: Ctrl+C)...\n")

    msg_counter = 0

    try:
        while True:
            # Cteni radku ze seriove linky
            raw_line = ser.readline()
            if not raw_line:
                continue

            try:
                decoded_line = raw_line.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            if not decoded_line:
                continue

            # Validace JSON formatu
            telemetry_data = validate_drybox_json(decoded_line)
            if telemetry_data is not None:
                msg_counter += 1

                # Doplneni textoveho statusu a typu pro webovy dashboard, pokud chybi
                if "status" not in telemetry_data:
                    state_map = {0: "idle", 1: "drying", 2: "target reached", 3: "error"}
                    telemetry_data["status"] = state_map.get(telemetry_data.get("dry_state", 1), "drying")
                if "type" not in telemetry_data:
                    telemetry_data["type"] = "PLA"

                payload_str = json.dumps(telemetry_data)

                # Publikace do MQTT (vychozi topic drybox/status/1)
                pub_info = client.publish(args.topic, payload_str, qos=0)
                pub_info.wait_for_publish(timeout=1.0)

                state_desc = {0: "Standby", 1: "Heating", 2: "Target", 3: "Error"}.get(
                    telemetry_data.get("dry_state", 0), "Unknown"
                )

                print(
                    f"[{msg_counter:04d}] [MQTT -> {args.topic}] "
                    f"Box #{telemetry_data['id']} | "
                    f"Teplota: {telemetry_data['temp']:.1f} °C | "
                    f"Vlhkost: {telemetry_data['hum']:.1f} % | "
                    f"Hmotnost: {telemetry_data['weight']:.2f} g | "
                    f"Stav: {state_desc}"
                )
            else:
                # Vypis neznamych / ladicich radku ze serioveho rozhrani
                print(f"[DEBUG LOG] {decoded_line}")

    except KeyboardInterrupt:
        print("\n[*] Preruseni uzivatelem (Ctrl+C). Ukoncuji...")

    finally:
        print("[*] Uzaviram seriovy port a MQTT spojeni...")
        if "ser" in locals() and ser.is_open:
            ser.close()
        client.loop_stop()
        client.disconnect()
        print("[*] Hotovo. Nashledanou.")


if __name__ == "__main__":
    main()

