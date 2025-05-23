#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "sdkconfig.h"

SemaphoreHandle_t xMutex;

void aliceTask(void *pvParameters) {
    xSemaphoreTake(xMutex, portMAX_DELAY);
    printf("Alice: took the mutex, doing long task...\n");

    // Simulate long task
    for (int i = 0; i < 10; i++) {
        printf("Alice: working... (%d)\n", i);
        vTaskDelay(pdMS_TO_TICKS(500));  // Total 5 seconds
    }

    printf("Alice: releasing the mutex.\n");
    xSemaphoreGive(xMutex);

    vTaskDelete(NULL);
}

void bobTask(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(1000));  // Let Alice start first

    printf("Bob: trying to take the mutex (high priority)...\n");
    xSemaphoreTake(xMutex, portMAX_DELAY);
    printf("Bob: got the mutex!\n");

    xSemaphoreGive(xMutex);
    vTaskDelete(NULL);
}

void carolTask(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(1500));  // Let Bob start waiting first

    for (int i = 0; i < 5; i++) {
        printf("Carol: doing some work... (%d)\n", i);
        vTaskDelay(pdMS_TO_TICKS(500));  // Simulate CPU usage
    }

    vTaskDelete(NULL);
}

void app_main(void)
{
    // vTaskStartScheduler(); is not needed in ESP-IDF. ESP-IDF starts the scheduler automatically after app_main() returns.

   /*  xMutex = xSemaphoreCreateMutex();

    xTaskCreate(aliceTask, "Alice", 2048, NULL, 1, NULL);   // Düşük öncelik
    xTaskCreate(bobTask, "Bob", 2048, NULL, 3, NULL);       // Yüksek öncelik
    xTaskCreate(carolTask, "Carol", 2048, NULL, 2, NULL);   // Orta öncelik */

    printf("ssid is: %s\n", CONFIG_SSID);
    printf("password is: %s\n", CONFIG_PASSWORD);

}
