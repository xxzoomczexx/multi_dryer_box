#ifndef CONFIG_H
#define CONFIG_H

/**
 * @file config.h
 * @brief Konfigurace Wi-Fi a MQTT brokeru pro Master Node (Raspberry Pi Pico W / Pico 2 W)
 */

// ============================================================================
// Nastavení Wi-Fi připojení (Vyplňte vlastní údaje)
// ============================================================================
#ifndef WIFI_SSID
#define WIFI_SSID       "Womp"
#endif

#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD   "csbv2529"
#endif

// ============================================================================
// Nastavení MQTT Brokeru
// ============================================================================
#ifndef MQTT_BROKER_HOST
#define MQTT_BROKER_HOST "54.36.178.49"
#endif

#ifndef MQTT_BROKER_PORT
#define MQTT_BROKER_PORT 1883
#endif

#ifndef MQTT_TOPIC_STATUS
#define MQTT_TOPIC_STATUS "drybox/status/1"
#endif

#ifndef MQTT_TOPIC_CMD
#define MQTT_TOPIC_CMD    "drybox/commands"
#endif

#endif // CONFIG_H

