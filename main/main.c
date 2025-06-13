#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "sdkconfig.h"
#include "esp_wifi.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_wifi_types.h"  // Added for CSI data types
#include "esp_timer.h"

// subcarrier sayısını arttırmak için b/g/n ayarı yapmam lazım!!! unutma

static const char *TAG = "csi_example";

// WiFi credentials
#define WIFI_SSID "hsgdsgsd"
#define WIFI_PASS "hsgsdfadg"

// CSI callback function - this gets called every time CSI data is received
//This is like a "listener" function - every time the ESP32 receives WiFi packets with CSI data, this function automatically gets called.
/* ctx (context): This is a generic pointer that lets you pass extra data to your callback. 
    Think of it like a "note" you can attach. We set it to NULL because we don't need it, 
    but you could pass a structure with your own data. */
static void wifi_csi_cb(void *ctx, wifi_csi_info_t *info){
    /*
    // Basic CSI information
    ESP_LOGI(TAG, "CSI Data Received!");
    ESP_LOGI(TAG, "RSSI: %d dBm", info->rx_ctrl.rssi); //(closer to 0 = stronger)
    ESP_LOGI(TAG, "Rate: %d", info->rx_ctrl.rate); //WiFi data rate/speed
    ESP_LOGI(TAG, "Channel: %d", info->rx_ctrl.channel);
    ESP_LOGI(TAG, "Bandwidth: %d", info->rx_ctrl.cwb); //0 = 20MHz channel width (normal)
    ESP_LOGI(TAG, "Data Length: %d bytes", info->len);
    */

    // Print CSI header info as JSON for easy Python parsing
    printf("CSI_START{");
    printf("\"rssi\":%d,", info->rx_ctrl.rssi);
    printf("\"rate\":%d,", info->rx_ctrl.rate);
    printf("\"channel\":%d,", info->rx_ctrl.channel);
    printf("\"bandwidth\":%d,", info->rx_ctrl.cwb);
    printf("\"len\":%d,", info->len);
    printf("\"timestamp\":%lld,", esp_timer_get_time()); // microseconds since boot
    
    // The actual CSI data is in info->buf
    // Output ALL CSI data as comma-separated values
    printf("\"csi_data\":[");
    if (info->buf && info->len > 0) {
        int8_t *csi_data = (int8_t *)info->buf;
        
        for (int i = 0; i < info->len; i++) {
            printf("%d", csi_data[i]);
            if (i < info->len - 1) {
                printf(",");
            }
        }
    }
    printf("]}CSI_END\n");
    
    // ESP_LOGI(TAG, "------------------------");

    ESP_LOGD(TAG, "CSI packet received - RSSI: %d, Length: %d", info->rx_ctrl.rssi, info->len);

}


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

    // NOW ENABLE CSI AFTER CONNECTION!
    ESP_LOGI(TAG, "Enabling CSI data collection...");
        
    // Step 1: Set up CSI configuration
    wifi_csi_config_t csi_config = {
        .lltf_en = true,        // Enable Long Training Field
        .htltf_en = true,       // Enable HT Long Training Field  
        .stbc_htltf2_en = true,        // Enable Space-Time Block Coding
        .ltf_merge_en = true,   // Enable LTF merging
        .channel_filter_en = false, // Disable channel filter for now
        .manu_scale = 0,        // Manual scaling (0 = auto)
    };
    
    // Step 2: Apply the CSI configuration
    esp_err_t ret = esp_wifi_set_csi_config(&csi_config);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to set CSI config: %s (0x%x)", esp_err_to_name(ret), ret);
            ESP_LOGE(TAG, "CSI might not be enabled in menuconfig!");
            ESP_LOGE(TAG, "Check: Component config -> Wi-Fi -> Enable CSI");
            return;
        } else {
            ESP_LOGI(TAG, "CSI config set successfully!");
    }
    
    // Step 3: Register our callback function
    // YES this is the way espressif intended. You create your own callback function, and pass it to esp_wifi_set_csi_rx_cb()
    ret = esp_wifi_set_csi_rx_cb(wifi_csi_cb, NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set CSI callback: %s", esp_err_to_name(ret));
        return;
    }
    
    // Step 4: Enable CSI data collection
    ret = esp_wifi_set_csi(true);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable CSI: %s", esp_err_to_name(ret));
        return;
    }
    
    ESP_LOGI(TAG, "CSI collection enabled successfully!");
}


void wifi_init_sta(void){

    /** INITIALIZE ALL THE THINGS **/
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
            .ssid = CONFIG_SSID,
            .password = CONFIG_PASSWORD,
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
        ESP_LOGI(TAG, "Hello from main loop");
        vTaskDelay(4000 / portTICK_PERIOD_MS); // Wait 1 second
    }

    //printf("ssid is: %s\n", CONFIG_SSID);
    //printf("password is: %s\n", CONFIG_PASSWORD);

}
