# LeForge formula-engine - Nintex K2 Integration

## Overview
LeForge plugin integration for Nintex K2.

## Installation

### 1. Register REST Service Broker

1. Open **K2 Management Console**
2. Navigate to **Integration** > **Service Types**
3. Add new **REST Service Broker**
4. Upload `swagger/formula-engine.json`
5. Configure base URL and authentication

### 2. Create Service Instance

1. Go to **Service Instances**
2. Create new instance from the registered service type
3. Configure connection:
   - Base URL: Your LeForge server URL
   - Authentication: API Key
   - Header: `X-API-Key`

### 3. Generate SmartObjects

1. Navigate to **SmartObjects**
2. Click **Generate SmartObjects** from service instance
3. Select operations to expose
4. Publish SmartObjects

## SmartObject Templates

Pre-configured SmartObject templates are available in the `smartobjects/` folder.
Import these for common operations.

## Available Operations

| SUM | Adds all numbers in a range |
| AVERAGE | Calculates the arithmetic mean of numbers |
| COUNT | Counts how many numbers are in a range |
| COUNTA | Counts non-empty values in a range |
| COUNTBLANK | Counts empty cells in a range |
| COUNTIF | Counts cells that meet a condition |
| COUNTIFS | Counts cells meeting multiple criteria |
| MAX | Returns the largest number in a range |
| MIN | Returns the smallest number in a range |
| MEDIAN | Returns the median of numbers |
| MODE | Returns the most frequently occurring value |
| STDEV | Calculates standard deviation (sample) |
| STDEVP | Calculates standard deviation (population) |
| VAR | Calculates variance (sample) |
| VARP | Calculates variance (population) |
| SUMIF | Sums values meeting a condition |
| SUMIFS | Sums values meeting multiple conditions |
| AVERAGEIF | Averages values meeting a condition |
| ROUND | Rounds a number to specified decimal places |
| ROUNDUP | Rounds a number up (away from zero) |

## Using in K2 Forms & Workflows

### In Forms
1. Add SmartObject data source
2. Bind to form controls
3. Execute methods on form events

### In Workflows
1. Add SmartObject event
2. Configure method and parameters
3. Map inputs/outputs

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
