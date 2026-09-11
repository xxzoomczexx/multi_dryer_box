#ifndef _LWIPOPTS_H
#define _LWIPOPTS_H

// Konfigurace lwIP pro Raspberry Pi Pico SDK (Pico W / Pico 2 W)

#ifndef NO_SYS
#define NO_SYS                      1
#endif

#ifndef LWIP_SOCKET
#define LWIP_SOCKET                 0
#endif

#if PICO_CYW43_ARCH_POLL
#define MEM_LIBC_MALLOC             1
#else
#define MEM_LIBC_MALLOC             0
#endif

#define MEM_ALIGNMENT               4
#define MEM_SIZE                    16000
#define MEMP_NUM_SYS_TIMEOUT        16
#define MEMP_NUM_TCP_SEG            32
#define MEMP_NUM_ARP_QUEUE          10
#define PBUF_POOL_SIZE              24

#define LWIP_ARP                    1
#define LWIP_ETHERNET               1
#define LWIP_ICMP                   1
#define LWIP_RAW                    1
#define TCP_WND                     (8 * TCP_MSS)
#define TCP_MSS                     1460
#define TCP_SND_BUF                 (8 * TCP_MSS)
#define TCP_SND_QUEUELEN            ((4 * (TCP_SND_BUF) + (TCP_MSS - 1)) / (TCP_MSS))

#define LWIP_NETIF_STATUS_CALLBACK  1
#define LWIP_NETIF_LINK_CALLBACK    1
#define LWIP_NETIF_HOSTNAME         1

#define LWIP_CHKSUM_ALGORITHM       3

// Podpora pro TCP, UDP, DNS, DHCP a MQTT
#define LWIP_TCP                    1
#define LWIP_UDP                    1
#define LWIP_DNS                    1
#define LWIP_DHCP                   1
#define LWIP_AUTOIP                 1
#define LWIP_DHCP_AUTOIP_COOP       1
#define LWIP_IGMP                   1
#define LWIP_TCP_KEEPALIVE          1

#define LWIP_NETCONN                0

// Debugging nastavení
#define LWIP_DEBUG                  0

#endif /* _LWIPOPTS_H */

