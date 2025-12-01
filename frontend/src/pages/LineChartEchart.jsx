import React from "react";
import ReactECharts from "echarts-for-react";

export default function LineChartEchart({ 
  data = [], 
  title = "", 
  height = 300,
  color = "#7163BA",
  xAxisKey = "name",
  yAxisKey = "value"
}) {
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#E5E7EB',
      borderWidth: 1,
      textStyle: {
        color: '#1F2937',
        fontSize: 12
      },
      padding: 12,
      formatter: function(params) {
        if (params && params.length > 0) {
          const value = params[0].value;
          const formattedValue = typeof value === 'number' 
            ? `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}` 
            : value;
          return `${params[0].name}<br/><strong>${formattedValue}</strong>`;
        }
        return '';
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item[xAxisKey]),
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: '#E5E7EB'
        }
      },
      axisLabel: {
        color: '#6B7280',
        fontSize: 11,
        rotate: 45,
        interval: 0
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: '#F3F4F6',
          type: 'dashed'
        }
      },
      axisLabel: {
        color: '#6B7280',
        fontSize: 11,
        formatter: function(value) {
          if (value >= 1000000) {
            return `$${(value / 1000000).toFixed(1)}M`;
          } else if (value >= 1000) {
            return `$${(value / 1000).toFixed(0)}K`;
          }
          return `$${value}`;
        }
      }
    },
    series: [
      {
        name: title,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        sampling: 'lttb',
        itemStyle: {
          color: color,
          borderWidth: 2,
          borderColor: '#FFFFFF'
        },
        lineStyle: {
          width: 3,
          color: color,
          shadowColor: `${color}40`,
          shadowBlur: 10,
          shadowOffsetY: 5
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: `${color}80` // 50% opacity at top
              },
              {
                offset: 1,
                color: `${color}10` // 6% opacity at bottom
              }
            ]
          }
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: color,
            borderWidth: 3,
            borderColor: '#FFFFFF',
            shadowBlur: 10,
            shadowColor: color
          }
        },
        data: data.map(item => item[yAxisKey])
      }
    ]
  };

  return (
    <ReactECharts 
      option={option} 
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'canvas' }}
    />
  );
}