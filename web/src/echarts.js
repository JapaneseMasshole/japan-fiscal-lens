// Tree-shaken ECharts: register only what the site uses. Add chart types here as needed.
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart, TreemapChart, SankeyChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DatasetComponent,
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  TreemapChart,
  SankeyChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DatasetComponent,
  MarkLineComponent, // reference lines: zero, averages, legal thresholds
  CanvasRenderer,
])

export default echarts
