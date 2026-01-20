# FlowForge formula-engine - Nintex Workflow Cloud Xtension

## Overview
FlowForge plugin Xtension for Nintex Workflow Cloud.

## Installation

1. Go to **Nintex Workflow Cloud** > **Settings** > **Xtensions**
2. Click **Add Xtension**
3. Choose **Add custom connector**
4. Upload `formula-engine.swagger.json`
5. Configure authentication (API Key)
6. Click **Publish**

## Configuration

### API Key Setup
1. In the Xtension settings, select **API Key** authentication
2. Set header name: `X-API-Key`
3. Enter your FlowForge API key

### Base URL
Update the host in the Swagger file to your FlowForge instance URL.

## Available Actions

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

## Usage in Workflows

After publishing the Xtension:
1. Open workflow designer
2. Find actions under **FlowForge** category
3. Drag and drop actions into your workflow
4. Configure action parameters

## Support

For issues or questions, visit [FlowForge Support](https://flowforge.io/support)
