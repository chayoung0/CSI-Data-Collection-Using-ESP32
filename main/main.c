#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

SemaphoreHandle_t xSemaphore;

void vTask1(void *pvParameters) {
    while(1) {
        if (xSemaphoreTake(xSemaphore, portMAX_DELAY)) {
            printf("Task1 got the semaphore!\n");
            xSemaphoreGive(xSemaphore);  // Give it back
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }
}

void vTask2(void *pvParameters) {
    while(1) {
        if (xSemaphoreTake(xSemaphore, portMAX_DELAY)) {
            printf("Task2 got the semaphore!\n");
            xSemaphoreGive(xSemaphore);  // Give it back
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }
}

void app_main(void)
{
    // vTaskStartScheduler(); is not needed in ESP-IDF. ESP-IDF starts the scheduler automatically after app_main() returns.

    xSemaphore = xSemaphoreCreateBinary();
    xSemaphoreGive(xSemaphore); // Initial release (so someone can take it)

    xTaskCreate(vTask1, "Task1", 2048, NULL, 1, NULL);
    xTaskCreate(vTask2, "Task2", 2048, NULL, 1, NULL);

}