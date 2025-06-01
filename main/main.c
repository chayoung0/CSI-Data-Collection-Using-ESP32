#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "sdkconfig.h"
#include "esp_wifi.h"
#include "esp_log.h"
#include "nvs_flash.h"

static const char *TAG = "wifi_example";

// WiFi credentials
#define WIFI_SSID "gdsgfsdhjsfgs"
#define WIFI_PASS "gdfhsgdgsg"

static void event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data){
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        // WiFi started, now try to connect
        esp_wifi_connect();
        ESP_LOGI(TAG, "WiFi started, trying to connect...");
    } 
    else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        // Lost connection, try to reconnect
        esp_wifi_connect();
        ESP_LOGI(TAG, "Disconnected, trying to reconnect...");
    } 
    else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        // Successfully connected and got an IP address!
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Connected! IP Address: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}

void wifi_init_sta(void){

    //Initialize NVS
    esp_err_t ret = nvs_flash_init(); //Creates storage space for WiFi settings
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    //Initialize the TCP/IP stack
    ESP_ERROR_CHECK(esp_netif_init()); //Sets up internet protocols

    //initialize default esp event loop
	ESP_ERROR_CHECK(esp_event_loop_create_default()); //Creates a message system so different parts can talk to each other

    //Create a WiFi station interface
    esp_netif_create_default_wifi_sta(); //Creates a WiFi client (STAtion)
    
    //Initialize WiFi with default configuration
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg)); //Turns on the WiFi chip inside the ESP32

    /** EVENT LOOP CRAZINESS **/
    //Register our event handler to listen for WiFi events
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL)); // This is a function pointer!
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL));
    //esp_event_handler_register() - Tell the ESP32 "when something WiFi-related happens, call my function"
    //The event_handler function responds to WiFi events like "started", "connected", "disconnected"

    //Configure WiFi settings
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK, // Security type
        },
    };

    //set the wifi controller to be a station
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));

    //Give the ESP32 your WiFi credentials
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));

    //Actually start trying to connect
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "WiFi initialization finished!");

    /** NOW WE WAIT **/

}

void app_main(void)
{
    // vTaskStartScheduler(); is not needed in ESP-IDF. ESP-IDF starts the scheduler automatically after app_main() returns.

    ESP_LOGI(TAG, "Starting WiFi example...");

    // Initialize and start WiFi
    wifi_init_sta();

    // Keep the program running - otherwise watchdog gets angryyyy
    while(1) {
        vTaskDelay(1000 / portTICK_PERIOD_MS); // Wait 1 second
    }

    //printf("ssid is: %s\n", CONFIG_SSID);
    //printf("password is: %s\n", CONFIG_PASSWORD);

}
