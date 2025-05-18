#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void vTask1(void *pvParameters) {
    for(int i=0; i<5; i++){
        printf("Task1: %d\n", i);
        vTaskDelay(pdMS_TO_TICKS(1000)); // Delay for 1000 ms
    }
    vTaskDelete(NULL); // Cleanly delete task when done
}

void vTask2(void *pvParameters) {
    for(int i=0; i<10; i++){
        printf("Task2: %d\n", i);
        vTaskDelay(pdMS_TO_TICKS(1000)); // Delay for 1000 ms
    }
    vTaskDelete(NULL); // Cleanly delete task when done
}

void app_main(void)
{
    // vTaskStartScheduler(); is not needed in ESP-IDF. ESP-IDF starts the scheduler automatically after app_main() returns.

    xTaskCreate(vTask1, "Task 1", 2048, NULL, 1, NULL);
    xTaskCreate(vTask2, "Task 2", 2048, NULL, 2, NULL);

}