<template>
  <AppPage :show-footer="true">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>{{ $t('views.workbench.text_welcome') }}</p>
            </div>
          </div>

          <div flex-col items-center>
            <div text-20 font-semibold mb-2>订 单 统 计</div>
            <!-- 创建等间距的布局容器 :size="12" 设置子元素之间的间距为 12px :wrap="false" 禁止换行 -->
            <n-space :size="12" :wrap="false">
              <n-statistic v-for="item in statisticData" :key="item.id" v-bind="item"></n-statistic>
            </n-space>
          </div>
        </div>
      </n-card>

      <!-- 卡片区域 -->
      <n-card title="新增统计" size="small" :segmented="true" mt-15 rounded-10>
        <n-grid :x-gap="36" :y-gap="12" :cols="3" item-responsive justify-items-center>
          <n-grid-item v-for="(card, index) in cards" :key="index">
            <n-card size="small" :bordered="false">
              <div flex justify-start gap-30>
                <div>
                  <div flex items-center gap-2 mb-2>
                    <span text-16>{{ card.title }}</span>
                    <TheIcon :icon="card.icon" :size="18" :color="card.color" />
                  </div>
                  <div text-24 font-bold mb-2 text-center>{{ card.number }}</div>
                  <div text-14>
                    <span text-green-500>{{ card.trend }}</span>
                    <span text-gray-500 ml-2>较昨天</span>
                  </div>
                </div>
                <div h-60 w-120 :ref="(el) => (trendRefs[index] = el)"></div>
              </div>
            </n-card>
          </n-grid-item>
        </n-grid>
      </n-card>
      <!-- 图表区域 -->
      <n-card size="small" :bordered="false" mt-15 rounded-10>
        <template #header>
          <div flex justify-between items-center>
            <span>交互统计</span>
            <n-radio-group v-model:value="statType" size="small">
              <n-radio-button value="chat">对话量</n-radio-button>
              <n-radio-button value="consume">新增量</n-radio-button>
            </n-radio-group>
          </div>
        </template>
        <div ref="chartRef" h-300></div>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useUserStore } from '@/store'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'
import { getStartOfDayTimestamp, getEndOfDayTimestamp, formatTimestamp } from '@/utils'

const userStore = useUserStore()

const statisticData = ref([])

async function fetchStatisticData() {
  try {
    const res = await api.getRechargeList({
      page: 1,
      page_size: 999999,
    })
    let amount = 0
    let paidCount = 0
    let notPaidCount = 0
    res.data.forEach((item) => {
      if (item.is_paid) {
        paidCount++
        amount += item.amount
      } else {
        notPaidCount++
      }
    })

    statisticData.value = [
      { id: 0, label: '充值金额', value: amount },
      { id: 1, label: '已支付', value: paidCount },
      { id: 2, label: '未支付', value: notPaidCount },
    ]
  } catch (e) {
    // 这里可以做错误处理
    $message.error('获取统计数据失败，请稍后重试', e)
    statisticData.value = [
      { id: 0, label: '充值金额', value: 0 },
      { id: 1, label: '已支付', value: 0 },
      { id: 2, label: '未支付', value: 0 },
    ]
  }
}

// 模拟卡片数据
const trendRefs = ref([])
const cards = ref([])

// 获取卡片统计数据
async function fetchCardsData() {
  try {
    const [userRes, deviceRes, mcpRes] = await Promise.all([
      api.getUserList({ page: 1, page_size: 999999 }),
      api.getDeviceList({ page: 1, page_size: 999999 }),
      api.getMCPList({ page: 1, page_size: 999999 }),
    ])

    cards.value = [
      {
        title: '用户数量',
        number: userRes.total || '0',
        trend: '+88%',
        icon: 'fluent-color:person-feedback-16',
        color: '#409EFF',
        data: [820, 932, 901, 934, 1290, 1330, 1320],
      },
      {
        title: '设备数量',
        number: deviceRes.total || '0',
        trend: '+70%',
        icon: 'icon-park:devices',
        color: '#67C23A',
        data: [720, 832, 901, 934, 1290, 1330, 1320],
      },
      {
        title: 'MCP服务数量',
        number: mcpRes.total || '0',
        trend: '+99%',
        icon: 'icon-park:personal-collection',
        color: '#E6A23C',
        data: [620, 732, 801, 934, 1290, 1330, 1320],
      },
    ]
  } catch (e) {
    $message?.error('获取卡片数据失败，请稍后重试', e)
    cards.value = [
      {
        title: '用户数量',
        number: '0',
        trend: '0%',
        icon: 'fluent-color:person-feedback-16',
        color: '#409EFF',
        data: [820, 932, 901, 934, 1290, 1330, 1320],
      },
      {
        title: '设备数量',
        number: '0',
        trend: '0%',
        icon: 'icon-park:devices',
        color: '#67C23A',
        data: [720, 832, 901, 934, 1290, 1330, 1320],
      },
      {
        title: 'MCP服务数量',
        number: '0',
        trend: '0%',
        icon: 'icon-park:personal-collection',
        color: '#E6A23C',
        data: [620, 732, 801, 934, 1290, 1330, 1320],
      },
    ]
  }
}

const initTrendCharts = () => {
  trendRefs.value.forEach((el, index) => {
    if (!el || !cards.value[index]) return
    const chart = echarts.init(el)
    chart.setOption({
      grid: {
        top: 0,
        right: 0,
        bottom: 0,
        left: 0,
      },
      xAxis: {
        type: 'category',
        show: false,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        show: false,
      },
      series: [
        {
          type: 'line',
          data: cards.value[index].data,
          smooth: true,
          showSymbol: false,
          lineStyle: {
            width: 3,
            color: cards.value[index].color,
            shadowColor: cards.value[index].color,
            shadowBlur: 5,
          },
          areaStyle: null, // 移除填充区域
        },
      ],
    })
  })
}

function getLastDays(num = 7) {
  const days = []
  const start_times = []
  const end_times = []
  const today = new Date()
  for (let i = num - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(today.getDate() - i)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    days.push(`${mm}-${dd}`)
    start_times.push(formatTimestamp(getStartOfDayTimestamp(d)))
    end_times.push(formatTimestamp(getEndOfDayTimestamp(d)))
  }
  return { days, start_times, end_times }
}

// 交互统计数据
const statType = ref('chat')
const chartRef = ref(null)
const chartData = ref({
  xAxis: [],
  series: [
    { name: '对话次数', data: [] },
    { name: '对话人数', data: [] },
  ],
})

// 获取交互统计数据
async function fetchChartData() {
  const { days, start_times, end_times } = getLastDays(7)
  // 清空数据，防止累加
  chartData.value.series[0].data = []
  chartData.value.series[1].data = []
  if (statType.value === 'chat') {
    chartData.value.series[0].name = '对话次数'
    chartData.value.series[1].name = '对话人数'
    try {
      // 获取所有对话数据
      const res = await api.getConversationList({
        page: 1,
        page_size: 999999,
      })
      // 按天统计对话次数和人数
      for (let i = 0; i < days.length; i++) {
        const startTime = new Date(start_times[i])
        const endTime = new Date(end_times[i])
        const dayConversations = res.data.filter((item) => {
          const itemDate = new Date(item.create_at)
          return itemDate >= startTime && itemDate <= endTime
        })
        const dialogCount = dayConversations.length
        const uniqueUsers = new Set(dayConversations.map((item) => item.user_id))
        chartData.value.series[0].data.push(dialogCount)
        chartData.value.series[1].data.push(uniqueUsers.size)
      }
      chartData.value.xAxis = days
      initChart()
    } catch (e) {
      $message?.error('获取对话统计数据失败，请稍后重试', e)
    }
  } else {
    chartData.value.series[0].name = '新增用户'
    chartData.value.series[1].name = '新增设备'
    try {
      // 获取最近7天的所有用户和设备数据
      const [userRes, deviceRes] = await Promise.all([
        api.getUserList({ page: 1, page_size: 999999 }),
        api.getDeviceList({ page: 1, page_size: 999999 }),
      ])
      // 按天统计新增用户和设备数
      for (let i = 0; i < days.length; i++) {
        const startTime = new Date(start_times[i])
        const endTime = new Date(end_times[i])
        const dayUsers = userRes.data.filter((item) => {
          const itemDate = new Date(item.create_at)
          return itemDate >= startTime && itemDate <= endTime
        })
        const dayDevices = deviceRes.data.filter((item) => {
          const itemDate = new Date(item.create_at)
          return itemDate >= startTime && itemDate <= endTime
        })
        chartData.value.series[0].data.push(dayUsers.length)
        chartData.value.series[1].data.push(dayDevices.length)
      }
      chartData.value.xAxis = days
      initChart()
    } catch (e) {
      $message?.error('获取新增统计数据失败，请稍后重试', e)
    }
  }
}

let chartInstance = null
function initChart() {
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: [chartData.value.series[0].name, chartData.value.series[1].name] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: chartData.value.xAxis },
    yAxis: { type: 'value' },
    series: [
      {
        name: chartData.value.series[0].name,
        type: 'bar',
        data: chartData.value.series[0].data,
        color: '#409EFF',
        barWidth: 24,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
      },
      {
        name: chartData.value.series[1].name,
        type: 'bar',
        data: chartData.value.series[1].data,
        color: '#FF9F43',
        barWidth: 24,
        itemStyle: { borderRadius: [6, 6, 0, 0] },
      },
    ],
  }
  chartInstance.setOption(option)
}

// 监听 statType 切换
watch(statType, fetchChartData)

onMounted(async () => {
  await fetchStatisticData()
  await fetchCardsData()
  initTrendCharts()
  await fetchChartData()
})
</script>
