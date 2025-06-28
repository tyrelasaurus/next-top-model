'use client';

import { useEffect, useRef } from 'react';

interface DataPoint {
  label: string;
  value: number;
  color?: string;
}

interface SimpleChartProps {
  data: DataPoint[];
  type: 'bar' | 'pie' | 'line';
  title?: string;
  width?: number;
  height?: number;
}

export function SimpleChart({ data, type, title, width = 400, height = 300 }: SimpleChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;

    if (type === 'bar') {
      drawBarChart(ctx, data, padding, chartWidth, chartHeight);
    } else if (type === 'pie') {
      drawPieChart(ctx, data, width / 2, height / 2, Math.min(chartWidth, chartHeight) / 2 - 20);
    } else if (type === 'line') {
      drawLineChart(ctx, data, padding, chartWidth, chartHeight);
    }

    // Draw title
    if (title) {
      ctx.fillStyle = '#374151';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(title, width / 2, 20);
    }
  }, [data, type, title, width, height]);

  const drawBarChart = (ctx: CanvasRenderingContext2D, data: DataPoint[], padding: number, chartWidth: number, chartHeight: number) => {
    const maxValue = Math.max(...data.map(d => d.value));
    const barWidth = chartWidth / data.length * 0.8;
    const barSpacing = chartWidth / data.length * 0.2;

    data.forEach((point, index) => {
      const barHeight = (point.value / maxValue) * chartHeight;
      const x = padding + index * (barWidth + barSpacing) + barSpacing / 2;
      const y = padding + chartHeight - barHeight;

      // Draw bar
      ctx.fillStyle = point.color || '#3B82F6';
      ctx.fillRect(x, y, barWidth, barHeight);

      // Draw label
      ctx.fillStyle = '#6B7280';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(point.label, x + barWidth / 2, padding + chartHeight + 15);

      // Draw value
      ctx.fillStyle = '#374151';
      ctx.fillText(point.value.toString(), x + barWidth / 2, y - 5);
    });
  };

  const drawPieChart = (ctx: CanvasRenderingContext2D, data: DataPoint[], centerX: number, centerY: number, radius: number) => {
    const total = data.reduce((sum, point) => sum + point.value, 0);
    let currentAngle = -Math.PI / 2;

    const colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];

    data.forEach((point, index) => {
      const sliceAngle = (point.value / total) * 2 * Math.PI;
      
      // Draw slice
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
      ctx.closePath();
      ctx.fillStyle = point.color || colors[index % colors.length];
      ctx.fill();

      // Draw label
      const labelAngle = currentAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius + 20);
      const labelY = centerY + Math.sin(labelAngle) * (radius + 20);
      
      ctx.fillStyle = '#374151';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${point.label} (${point.value})`, labelX, labelY);

      currentAngle += sliceAngle;
    });
  };

  const drawLineChart = (ctx: CanvasRenderingContext2D, data: DataPoint[], padding: number, chartWidth: number, chartHeight: number) => {
    if (data.length < 2) return;

    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = Math.min(...data.map(d => d.value));
    const valueRange = maxValue - minValue || 1;

    const points = data.map((point, index) => ({
      x: padding + (index / (data.length - 1)) * chartWidth,
      y: padding + chartHeight - ((point.value - minValue) / valueRange) * chartHeight
    }));

    // Draw line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.slice(1).forEach(point => {
      ctx.lineTo(point.x, point.y);
    });
    ctx.strokeStyle = '#3B82F6';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw points and labels
    points.forEach((point, index) => {
      // Draw point
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = '#3B82F6';
      ctx.fill();

      // Draw label
      ctx.fillStyle = '#6B7280';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(data[index].label, point.x, padding + chartHeight + 15);

      // Draw value
      ctx.fillStyle = '#374151';
      ctx.fillText(data[index].value.toString(), point.x, point.y - 10);
    });
  };

  return (
    <div className="flex justify-center">
      <canvas 
        ref={canvasRef} 
        width={width} 
        height={height}
        className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
      />
    </div>
  );
}