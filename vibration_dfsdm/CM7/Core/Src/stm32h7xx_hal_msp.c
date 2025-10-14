/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file         stm32h7xx_hal_msp.c
  * @brief        This file provides code for the MSP Initialization
  *               and de-Initialization codes.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */
extern DMA_HandleTypeDef hdma_dac1_ch1;

extern DMA_HandleTypeDef hdma_dfsdm1_flt0;

extern DMA_HandleTypeDef hdma_dfsdm1_flt1;

extern DMA_HandleTypeDef hdma_dfsdm1_flt2;

extern DMA_HandleTypeDef hdma_dfsdm1_flt3;

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN TD */

/* USER CODE END TD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN Define */

/* USER CODE END Define */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN Macro */

/* USER CODE END Macro */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* External functions --------------------------------------------------------*/
/* USER CODE BEGIN ExternalFunctions */

/* USER CODE END ExternalFunctions */

/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);
                    /**
  * Initializes the Global MSP.
  */
void HAL_MspInit(void)
{

  /* USER CODE BEGIN MspInit 0 */

  /* USER CODE END MspInit 0 */

  __HAL_RCC_SYSCFG_CLK_ENABLE();

  /* System interrupt init*/

  /* USER CODE BEGIN MspInit 1 */

  /* USER CODE END MspInit 1 */
}

/**
  * @brief DAC MSP Initialization
  * This function configures the hardware resources used in this example
  * @param hdac: DAC handle pointer
  * @retval None
  */
void HAL_DAC_MspInit(DAC_HandleTypeDef* hdac)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  if(hdac->Instance==DAC1)
  {
    /* USER CODE BEGIN DAC1_MspInit 0 */

    /* USER CODE END DAC1_MspInit 0 */
    /* Peripheral clock enable */
    __HAL_RCC_DAC12_CLK_ENABLE();

    __HAL_RCC_GPIOA_CLK_ENABLE();
    /**DAC1 GPIO Configuration
    PA4     ------> DAC1_OUT1
    */
    GPIO_InitStruct.Pin = GPIO_PIN_4;
    GPIO_InitStruct.Mode = GPIO_MODE_ANALOG;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* DAC1 DMA Init */
    /* DAC1_CH1 Init */
    hdma_dac1_ch1.Instance = DMA2_Stream0;
    hdma_dac1_ch1.Init.Request = DMA_REQUEST_DAC1;
    hdma_dac1_ch1.Init.Direction = DMA_MEMORY_TO_PERIPH;
    hdma_dac1_ch1.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_dac1_ch1.Init.MemInc = DMA_MINC_ENABLE;
    hdma_dac1_ch1.Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
    hdma_dac1_ch1.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
    hdma_dac1_ch1.Init.Mode = DMA_CIRCULAR;
    hdma_dac1_ch1.Init.Priority = DMA_PRIORITY_VERY_HIGH;
    hdma_dac1_ch1.Init.FIFOMode = DMA_FIFOMODE_DISABLE;
    if (HAL_DMA_Init(&hdma_dac1_ch1) != HAL_OK)
    {
      Error_Handler();
    }

    __HAL_LINKDMA(hdac,DMA_Handle1,hdma_dac1_ch1);

    /* DAC1 interrupt Init */
    HAL_NVIC_SetPriority(TIM6_DAC_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);
    /* USER CODE BEGIN DAC1_MspInit 1 */

    /* USER CODE END DAC1_MspInit 1 */

  }

}

/**
  * @brief DAC MSP De-Initialization
  * This function freeze the hardware resources used in this example
  * @param hdac: DAC handle pointer
  * @retval None
  */
void HAL_DAC_MspDeInit(DAC_HandleTypeDef* hdac)
{
  if(hdac->Instance==DAC1)
  {
    /* USER CODE BEGIN DAC1_MspDeInit 0 */

    /* USER CODE END DAC1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_DAC12_CLK_DISABLE();

    /**DAC1 GPIO Configuration
    PA4     ------> DAC1_OUT1
    */
    HAL_GPIO_DeInit(GPIOA, GPIO_PIN_4);

    /* DAC1 DMA DeInit */
    HAL_DMA_DeInit(hdac->DMA_Handle1);

    /* DAC1 interrupt DeInit */
    HAL_NVIC_DisableIRQ(TIM6_DAC_IRQn);
    /* USER CODE BEGIN DAC1_MspDeInit 1 */

    /* USER CODE END DAC1_MspDeInit 1 */
  }

}

static uint32_t HAL_RCC_DFSDM1_CLK_ENABLED=0;

static uint32_t DFSDM1_Init = 0;
/**
  * @brief DFSDM_Filter MSP Initialization
  * This function configures the hardware resources used in this example
  * @param hdfsdm_filter: DFSDM_Filter handle pointer
  * @retval None
  */
void HAL_DFSDM_FilterMspInit(DFSDM_Filter_HandleTypeDef* hdfsdm_filter)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInitStruct = {0};
  if(DFSDM1_Init == 0)
  {
    /* USER CODE BEGIN DFSDM1_MspInit 0 */

    /* USER CODE END DFSDM1_MspInit 0 */

  /** Initializes the peripherals clock
  */
    PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_DFSDM1;
    PeriphClkInitStruct.Dfsdm1ClockSelection = RCC_DFSDM1CLKSOURCE_D2PCLK1;
    if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct) != HAL_OK)
    {
      Error_Handler();
    }

    /* Peripheral clock enable */
    HAL_RCC_DFSDM1_CLK_ENABLED++;
    if(HAL_RCC_DFSDM1_CLK_ENABLED==1){
      __HAL_RCC_DFSDM1_CLK_ENABLE();
    }

    __HAL_RCC_GPIOE_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    /**DFSDM1 GPIO Configuration
    PE4     ------> DFSDM1_DATIN3
    PC0     ------> DFSDM1_DATIN4
    PC2_C     ------> DFSDM1_CKOUT
    PC3_C     ------> DFSDM1_DATIN1
    PE7     ------> DFSDM1_DATIN2
    */
    GPIO_InitStruct.Pin = GPIO_PIN_4|GPIO_PIN_7;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF3_DFSDM1;
    HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_0|GPIO_PIN_2;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF6_DFSDM1;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_3;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF3_DFSDM1;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

    /* USER CODE BEGIN DFSDM1_MspInit 1 */

    /* USER CODE END DFSDM1_MspInit 1 */

  DFSDM1_Init++;
  }

    /* DFSDM1 DMA Init */
    /* DFSDM1_FLT0 Init */
  if(hdfsdm_filter->Instance == DFSDM1_Filter0){
    hdma_dfsdm1_flt0.Instance = DMA1_Stream0;
    hdma_dfsdm1_flt0.Init.Request = DMA_REQUEST_DFSDM1_FLT0;
    hdma_dfsdm1_flt0.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_dfsdm1_flt0.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_dfsdm1_flt0.Init.MemInc = DMA_MINC_ENABLE;
    hdma_dfsdm1_flt0.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
    hdma_dfsdm1_flt0.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
    hdma_dfsdm1_flt0.Init.Mode = DMA_CIRCULAR;
    hdma_dfsdm1_flt0.Init.Priority = DMA_PRIORITY_HIGH;
    hdma_dfsdm1_flt0.Init.FIFOMode = DMA_FIFOMODE_ENABLE;
    hdma_dfsdm1_flt0.Init.FIFOThreshold = DMA_FIFO_THRESHOLD_FULL;
    hdma_dfsdm1_flt0.Init.MemBurst = DMA_MBURST_INC4;
    hdma_dfsdm1_flt0.Init.PeriphBurst = DMA_PBURST_SINGLE;
    if (HAL_DMA_Init(&hdma_dfsdm1_flt0) != HAL_OK)
    {
      Error_Handler();
    }

    /* Several peripheral DMA handle pointers point to the same DMA handle.
     Be aware that there is only one channel to perform all the requested DMAs. */
    __HAL_LINKDMA(hdfsdm_filter,hdmaInj,hdma_dfsdm1_flt0);
    __HAL_LINKDMA(hdfsdm_filter,hdmaReg,hdma_dfsdm1_flt0);
  }

    /* DFSDM1_FLT1 Init */
  if(hdfsdm_filter->Instance == DFSDM1_Filter1){
    hdma_dfsdm1_flt1.Instance = DMA1_Stream1;
    hdma_dfsdm1_flt1.Init.Request = DMA_REQUEST_DFSDM1_FLT1;
    hdma_dfsdm1_flt1.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_dfsdm1_flt1.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_dfsdm1_flt1.Init.MemInc = DMA_MINC_ENABLE;
    hdma_dfsdm1_flt1.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
    hdma_dfsdm1_flt1.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
    hdma_dfsdm1_flt1.Init.Mode = DMA_CIRCULAR;
    hdma_dfsdm1_flt1.Init.Priority = DMA_PRIORITY_HIGH;
    hdma_dfsdm1_flt1.Init.FIFOMode = DMA_FIFOMODE_ENABLE;
    hdma_dfsdm1_flt1.Init.FIFOThreshold = DMA_FIFO_THRESHOLD_FULL;
    hdma_dfsdm1_flt1.Init.MemBurst = DMA_MBURST_INC4;
    hdma_dfsdm1_flt1.Init.PeriphBurst = DMA_PBURST_SINGLE;
    if (HAL_DMA_Init(&hdma_dfsdm1_flt1) != HAL_OK)
    {
      Error_Handler();
    }

    /* Several peripheral DMA handle pointers point to the same DMA handle.
     Be aware that there is only one channel to perform all the requested DMAs. */
    __HAL_LINKDMA(hdfsdm_filter,hdmaInj,hdma_dfsdm1_flt1);
    __HAL_LINKDMA(hdfsdm_filter,hdmaReg,hdma_dfsdm1_flt1);
  }

    /* DFSDM1_FLT2 Init */
  if(hdfsdm_filter->Instance == DFSDM1_Filter2){
    hdma_dfsdm1_flt2.Instance = DMA1_Stream2;
    hdma_dfsdm1_flt2.Init.Request = DMA_REQUEST_DFSDM1_FLT2;
    hdma_dfsdm1_flt2.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_dfsdm1_flt2.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_dfsdm1_flt2.Init.MemInc = DMA_MINC_ENABLE;
    hdma_dfsdm1_flt2.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
    hdma_dfsdm1_flt2.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
    hdma_dfsdm1_flt2.Init.Mode = DMA_CIRCULAR;
    hdma_dfsdm1_flt2.Init.Priority = DMA_PRIORITY_HIGH;
    hdma_dfsdm1_flt2.Init.FIFOMode = DMA_FIFOMODE_ENABLE;
    hdma_dfsdm1_flt2.Init.FIFOThreshold = DMA_FIFO_THRESHOLD_FULL;
    hdma_dfsdm1_flt2.Init.MemBurst = DMA_MBURST_INC4;
    hdma_dfsdm1_flt2.Init.PeriphBurst = DMA_PBURST_SINGLE;
    if (HAL_DMA_Init(&hdma_dfsdm1_flt2) != HAL_OK)
    {
      Error_Handler();
    }

    /* Several peripheral DMA handle pointers point to the same DMA handle.
     Be aware that there is only one channel to perform all the requested DMAs. */
    __HAL_LINKDMA(hdfsdm_filter,hdmaInj,hdma_dfsdm1_flt2);
    __HAL_LINKDMA(hdfsdm_filter,hdmaReg,hdma_dfsdm1_flt2);
  }

    /* DFSDM1_FLT3 Init */
  if(hdfsdm_filter->Instance == DFSDM1_Filter3){
    hdma_dfsdm1_flt3.Instance = DMA1_Stream3;
    hdma_dfsdm1_flt3.Init.Request = DMA_REQUEST_DFSDM1_FLT3;
    hdma_dfsdm1_flt3.Init.Direction = DMA_PERIPH_TO_MEMORY;
    hdma_dfsdm1_flt3.Init.PeriphInc = DMA_PINC_DISABLE;
    hdma_dfsdm1_flt3.Init.MemInc = DMA_MINC_ENABLE;
    hdma_dfsdm1_flt3.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
    hdma_dfsdm1_flt3.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
    hdma_dfsdm1_flt3.Init.Mode = DMA_CIRCULAR;
    hdma_dfsdm1_flt3.Init.Priority = DMA_PRIORITY_HIGH;
    hdma_dfsdm1_flt3.Init.FIFOMode = DMA_FIFOMODE_ENABLE;
    hdma_dfsdm1_flt3.Init.FIFOThreshold = DMA_FIFO_THRESHOLD_FULL;
    hdma_dfsdm1_flt3.Init.MemBurst = DMA_MBURST_INC4;
    hdma_dfsdm1_flt3.Init.PeriphBurst = DMA_PBURST_SINGLE;
    if (HAL_DMA_Init(&hdma_dfsdm1_flt3) != HAL_OK)
    {
      Error_Handler();
    }

    /* Several peripheral DMA handle pointers point to the same DMA handle.
     Be aware that there is only one channel to perform all the requested DMAs. */
    __HAL_LINKDMA(hdfsdm_filter,hdmaInj,hdma_dfsdm1_flt3);
    __HAL_LINKDMA(hdfsdm_filter,hdmaReg,hdma_dfsdm1_flt3);
  }

}

/**
  * @brief DFSDM_Channel MSP Initialization
  * This function configures the hardware resources used in this example
  * @param hdfsdm_channel: DFSDM_Channel handle pointer
  * @retval None
  */
void HAL_DFSDM_ChannelMspInit(DFSDM_Channel_HandleTypeDef* hdfsdm_channel)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInitStruct = {0};
  if(DFSDM1_Init == 0)
  {
    /* USER CODE BEGIN DFSDM1_MspInit 0 */

    /* USER CODE END DFSDM1_MspInit 0 */

  /** Initializes the peripherals clock
  */
    PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_DFSDM1;
    PeriphClkInitStruct.Dfsdm1ClockSelection = RCC_DFSDM1CLKSOURCE_D2PCLK1;
    if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct) != HAL_OK)
    {
      Error_Handler();
    }

    /* Peripheral clock enable */
    HAL_RCC_DFSDM1_CLK_ENABLED++;
    if(HAL_RCC_DFSDM1_CLK_ENABLED==1){
      __HAL_RCC_DFSDM1_CLK_ENABLE();
    }

    __HAL_RCC_GPIOE_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    /**DFSDM1 GPIO Configuration
    PE4     ------> DFSDM1_DATIN3
    PC0     ------> DFSDM1_DATIN4
    PC2_C     ------> DFSDM1_CKOUT
    PC3_C     ------> DFSDM1_DATIN1
    PE7     ------> DFSDM1_DATIN2
    */
    GPIO_InitStruct.Pin = GPIO_PIN_4|GPIO_PIN_7;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF3_DFSDM1;
    HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_0|GPIO_PIN_2;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF6_DFSDM1;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

    GPIO_InitStruct.Pin = GPIO_PIN_3;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF3_DFSDM1;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

    /* USER CODE BEGIN DFSDM1_MspInit 1 */

    /* USER CODE END DFSDM1_MspInit 1 */

  DFSDM1_Init++;
  }

}

/**
  * @brief DFSDM_Filter MSP De-Initialization
  * This function freeze the hardware resources used in this example
  * @param hdfsdm_filter: DFSDM_Filter handle pointer
  * @retval None
  */
void HAL_DFSDM_FilterMspDeInit(DFSDM_Filter_HandleTypeDef* hdfsdm_filter)
{
  DFSDM1_Init-- ;
  if(DFSDM1_Init == 0)
    {
    /* USER CODE BEGIN DFSDM1_MspDeInit 0 */

    /* USER CODE END DFSDM1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_DFSDM1_CLK_DISABLE();

    /**DFSDM1 GPIO Configuration
    PE4     ------> DFSDM1_DATIN3
    PC0     ------> DFSDM1_DATIN4
    PC2_C     ------> DFSDM1_CKOUT
    PC3_C     ------> DFSDM1_DATIN1
    PE7     ------> DFSDM1_DATIN2
    */
    HAL_GPIO_DeInit(GPIOE, GPIO_PIN_4|GPIO_PIN_7);

    HAL_GPIO_DeInit(GPIOC, GPIO_PIN_0|GPIO_PIN_2|GPIO_PIN_3);

    /* DFSDM1 DMA DeInit */
    HAL_DMA_DeInit(hdfsdm_filter->hdmaInj);
    HAL_DMA_DeInit(hdfsdm_filter->hdmaReg);
    /* USER CODE BEGIN DFSDM1_MspDeInit 1 */

    /* USER CODE END DFSDM1_MspDeInit 1 */
  }

}

/**
  * @brief DFSDM_Channel MSP De-Initialization
  * This function freeze the hardware resources used in this example
  * @param hdfsdm_channel: DFSDM_Channel handle pointer
  * @retval None
  */
void HAL_DFSDM_ChannelMspDeInit(DFSDM_Channel_HandleTypeDef* hdfsdm_channel)
{
  DFSDM1_Init-- ;
  if(DFSDM1_Init == 0)
    {
    /* USER CODE BEGIN DFSDM1_MspDeInit 0 */

    /* USER CODE END DFSDM1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_DFSDM1_CLK_DISABLE();

    /**DFSDM1 GPIO Configuration
    PE4     ------> DFSDM1_DATIN3
    PC0     ------> DFSDM1_DATIN4
    PC2_C     ------> DFSDM1_CKOUT
    PC3_C     ------> DFSDM1_DATIN1
    PE7     ------> DFSDM1_DATIN2
    */
    HAL_GPIO_DeInit(GPIOE, GPIO_PIN_4|GPIO_PIN_7);

    HAL_GPIO_DeInit(GPIOC, GPIO_PIN_0|GPIO_PIN_2|GPIO_PIN_3);

    /* USER CODE BEGIN DFSDM1_MspDeInit 1 */

    /* USER CODE END DFSDM1_MspDeInit 1 */
  }

}

/**
  * @brief TIM_Base MSP Initialization
  * This function configures the hardware resources used in this example
  * @param htim_base: TIM_Base handle pointer
  * @retval None
  */
void HAL_TIM_Base_MspInit(TIM_HandleTypeDef* htim_base)
{
  if(htim_base->Instance==TIM1)
  {
    /* USER CODE BEGIN TIM1_MspInit 0 */

    /* USER CODE END TIM1_MspInit 0 */
    /* Peripheral clock enable */
    __HAL_RCC_TIM1_CLK_ENABLE();
    /* USER CODE BEGIN TIM1_MspInit 1 */

    /* USER CODE END TIM1_MspInit 1 */
  }
  else if(htim_base->Instance==TIM2)
  {
    /* USER CODE BEGIN TIM2_MspInit 0 */

    /* USER CODE END TIM2_MspInit 0 */
    /* Peripheral clock enable */
    __HAL_RCC_TIM2_CLK_ENABLE();
    /* USER CODE BEGIN TIM2_MspInit 1 */

    /* USER CODE END TIM2_MspInit 1 */
  }

}

void HAL_TIM_MspPostInit(TIM_HandleTypeDef* htim)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  if(htim->Instance==TIM2)
  {
    /* USER CODE BEGIN TIM2_MspPostInit 0 */

    /* USER CODE END TIM2_MspPostInit 0 */

    __HAL_RCC_GPIOA_CLK_ENABLE();
    /**TIM2 GPIO Configuration
    PA0     ------> TIM2_CH1
    */
    GPIO_InitStruct.Pin = GPIO_PIN_0;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF1_TIM2;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* USER CODE BEGIN TIM2_MspPostInit 1 */

    /* USER CODE END TIM2_MspPostInit 1 */
  }

}
/**
  * @brief TIM_Base MSP De-Initialization
  * This function freeze the hardware resources used in this example
  * @param htim_base: TIM_Base handle pointer
  * @retval None
  */
void HAL_TIM_Base_MspDeInit(TIM_HandleTypeDef* htim_base)
{
  if(htim_base->Instance==TIM1)
  {
    /* USER CODE BEGIN TIM1_MspDeInit 0 */

    /* USER CODE END TIM1_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_TIM1_CLK_DISABLE();
    /* USER CODE BEGIN TIM1_MspDeInit 1 */

    /* USER CODE END TIM1_MspDeInit 1 */
  }
  else if(htim_base->Instance==TIM2)
  {
    /* USER CODE BEGIN TIM2_MspDeInit 0 */

    /* USER CODE END TIM2_MspDeInit 0 */
    /* Peripheral clock disable */
    __HAL_RCC_TIM2_CLK_DISABLE();
    /* USER CODE BEGIN TIM2_MspDeInit 1 */

    /* USER CODE END TIM2_MspDeInit 1 */
  }

}

/* USER CODE BEGIN 1 */

/* USER CODE END 1 */
