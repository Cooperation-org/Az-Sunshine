import React, { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  DollarSign, 
  FileText, 
  RefreshCw,
  ArrowUpRight,
  MoreVertical,
  Calendar,
  Building2,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import api from "../api/api";
import Header from "../components/Header";
import { useDarkMode } from "../context/DarkModeContext";

export default function Dashboard() {
  const { darkMode } = useDarkMode();
  const [metrics, setMetrics] = useState({});
  const [chartsData, setChartsData] = useState(null);
  const [recentExpenditures, setRecentExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    await Promise.all([
      loadSummary(),
      loadChartsData(),
      loadRecentExpenditures()
    ]);
    setLoading(false);
  }

  async function loadSummary() {
    try {
      const data = await api.get('dashboard/summary-optimized/');
      setMetrics({
        total_expenditures: parseFloat(data.data.total_ie_spending || 0),
        num_candidates: data.data.candidate_committees || 0,
        num_expenditures: data.data.num_expenditures || 0,
        soi_stats: data.data.soi_tracking || {}
      });
    } catch (error) {
      console.error("Error loading summary:", error);
    }
  }

  async function loadChartsData() {
    try {
      const data = await api.get('dashboard/charts-data/');
      console.log("Charts data received:", data.data);
      setChartsData(data.data);
    } catch (error) {
      console.error("Error loading charts:", error);
    }
  }

  async function loadRecentExpenditures() {
    try {
      const data = await api.get('dashboard/recent-expenditures/');
      setRecentExpenditures(data.data.results || []);
    } catch (error) {
      console.error("Error loading expenditures:", error);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await api.post('dashboard/refresh-mv/');
      await loadDashboard();
    } catch (error) {
      console.error("Error refreshing:", error);
    } finally {
      setRefreshing(false);
    }
  }

  // Stat Cards Data
  const statCards = [
    {
      title: "Total IE Spending",
      value: `$${(metrics.total_expenditures || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      change: "+12.3%",
      trend: "up",
      subtitle: "+$3.14M vs last week",
      icon: DollarSign,
      color: "#7163BA",
    },
    {
      title: "Candidate Committees",
      value: (metrics.num_candidates || 0).toLocaleString(),
      change: "+24.6%",
      trend: "up",
      subtitle: "+806 vs last week",
      icon: Users,
      color: "#7163BA",
    },
    {
      title: "Total Expenditures",
      value: (metrics.num_expenditures || 0).toLocaleString(),
      change: "+5.8%",
      trend: "up",
      subtitle: "+249 this month",
      icon: FileText,
      color: "#7163BA",
    },
    {
      title: "SOI Filings",
      value: (metrics.soi_stats?.total_filings || 0).toLocaleString(),
      change: "-8.5%",
      trend: "down",
      subtitle: `${metrics.soi_stats?.uncontacted || 0} uncontacted`,
      icon: TrendingUp,
      color: "#800080",
    },
  ];

  // ECharts Options for Top Donors
  const topDonorsOption = {
    grid: {
      left: '5%',
      right: '5%',
      bottom: '8%',
      top: '10%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: darkMode ? 'rgba(51, 45, 84, 0.98)' : 'rgba(255, 255, 255, 0.98)',
      borderColor: darkMode ? '#4c3e7c' : '#E5E7EB',
      borderWidth: 1,
      textStyle: {
        color: darkMode ? '#ffffff' : '#1F2937',
        fontSize: 13
      },
      padding: 16,
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#7163BA'
        }
      },
      formatter: function(params) {
        if (params && params.length > 0) {
          const donorName = chartsData?.top_donors?.[params[0].dataIndex]?.entity_name || 'Unknown';
          const value = params[0].value;
          return `<div style="font-weight: 600; margin-bottom: 4px;">${donorName}</div><div style="color: #7163BA; font-size: 15px; font-weight: 700;">$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>`;
        }
        return '';
      }
    },
    xAxis: {
      type: 'category',
      data: chartsData?.top_donors?.map((d, idx) => `#${idx + 1}`).slice(0, 10) || [],
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: darkMode ? '#5f5482' : '#E5E7EB'
        }
      },
      axisLabel: {
        color: darkMode ? '#b8b3cc' : '#6B7280',
        fontSize: 12,
        fontWeight: 500
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
          color: darkMode ? '#5f5482' : '#F3F4F6',
          type: 'dashed'
        }
      },
      axisLabel: {
        color: darkMode ? '#b8b3cc' : '#6B7280',
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
        name: 'Contribution',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 10,
        sampling: 'lttb',
        itemStyle: {
          color: darkMode ? '#8b7cb8' : '#7163BA',
          borderWidth: 3,
          borderColor: darkMode ? '#3d3559' : '#FFFFFF'
        },
        lineStyle: {
          width: 3,
          color: darkMode ? '#8b7cb8' : '#7163BA',
          shadowColor: 'rgba(113, 99, 186, 0.3)',
          shadowBlur: 12,
          shadowOffsetY: 6
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
                color: darkMode ? 'rgba(139, 124, 184, 0.4)' : 'rgba(113, 99, 186, 0.4)'
              },
              {
                offset: 1,
                color: darkMode ? 'rgba(139, 124, 184, 0.05)' : 'rgba(113, 99, 186, 0.05)'
              }
            ]
          }
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: darkMode ? '#8b7cb8' : '#7163BA',
            borderWidth: 4,
            borderColor: darkMode ? '#3d3559' : '#FFFFFF',
            shadowBlur: 15,
            shadowColor: darkMode ? '#8b7cb8' : '#7163BA'
          }
        },
        data: chartsData?.top_donors?.map(d => Math.abs(parseFloat(d.total_contributed || 0))).slice(0, 10) || []
      }
    ]
  };

  // ECharts Options for Top Committees
  const topCommitteesOption = {
    grid: {
      left: '5%',
      right: '5%',
      bottom: '8%',
      top: '10%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: darkMode ? 'rgba(51, 45, 84, 0.98)' : 'rgba(255, 255, 255, 0.98)',
      borderColor: darkMode ? '#4c3e7c' : '#E5E7EB',
      borderWidth: 1,
      textStyle: {
        color: darkMode ? '#ffffff' : '#1F2937',
        fontSize: 13
      },
      padding: 16,
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#c084fc'
        }
      },
      formatter: function(params) {
        if (params && params.length > 0) {
          const committeeName = chartsData?.top_ie_committees?.[params[0].dataIndex]?.committee || 'Unknown';
          const value = params[0].value;
          return `<div style="font-weight: 600; margin-bottom: 4px;">${committeeName}</div><div style="color: #c084fc; font-size: 15px; font-weight: 700;">$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>`;
        }
        return '';
      }
    },
    xAxis: {
      type: 'category',
      data: chartsData?.top_ie_committees?.map((c, idx) => `#${idx + 1}`).slice(0, 10) || [],
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: darkMode ? '#5f5482' : '#E5E7EB'
        }
      },
      axisLabel: {
        color: darkMode ? '#b8b3cc' : '#6B7280',
        fontSize: 12,
        fontWeight: 500
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
          color: darkMode ? '#5f5482' : '#F3F4F6',
          type: 'dashed'
        }
      },
      axisLabel: {
        color: darkMode ? '#b8b3cc' : '#6B7280',
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
        name: 'Spending',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 10,
        sampling: 'lttb',
        itemStyle: {
          color: darkMode ? '#c084fc' : '#800080',
          borderWidth: 3,
          borderColor: darkMode ? '#3d3559' : '#FFFFFF'
        },
        lineStyle: {
          width: 3,
          color: darkMode ? '#c084fc' : '#800080',
          shadowColor: 'rgba(192, 132, 252, 0.3)',
          shadowBlur: 12,
          shadowOffsetY: 6
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
                color: darkMode ? 'rgba(192, 132, 252, 0.4)' : 'rgba(128, 0, 128, 0.4)'
              },
              {
                offset: 1,
                color: darkMode ? 'rgba(192, 132, 252, 0.05)' : 'rgba(128, 0, 128, 0.05)'
              }
            ]
          }
        },
        emphasis: {
          focus: 'series',
          itemStyle: {
            color: darkMode ? '#c084fc' : '#800080',
            borderWidth: 4,
            borderColor: darkMode ? '#3d3559' : '#FFFFFF',
            shadowBlur: 15,
            shadowColor: darkMode ? '#c084fc' : '#800080'
          }
        },
        data: (chartsData?.top_ie_committees || [])
          .slice(0, 10)
          .map(c => Math.abs(parseFloat(c.total_spending || c.total_ie || c.total_spent || c.total || 0)))
      }
    ]
  };



    // Doughnut Chart Options
  const benefitBreakdownOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: darkMode ? 'rgba(51, 45, 84, 0.98)' : 'rgba(255, 255, 255, 0.98)',
      borderColor: darkMode ? '#4c3e7c' : '#E5E7EB',
      borderWidth: 1,
      textStyle: {
        color: darkMode ? '#ffffff' : '#1F2937',
        fontSize: 13
      },
      padding: 16,
      formatter: function(params) {
        return `<div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div><div style="font-size: 15px; font-weight: 700; color: ${params.color};">$${params.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div><div style="color: #6B7280; font-size: 12px; margin-top: 2px;">${params.percent}%</div>`;
      }
    },
    legend: {
      show: false
    },
    series: [
      {
        name: 'IE Benefit',
        type: 'pie',
        radius: ['55%', '85%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: darkMode ? '#3d3559' : '#fff',
          borderWidth: 4
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: false
          },
          itemStyle: {
            shadowBlur: 20,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.15)'
          },
          scale: true,
          scaleSize: 8
        },
        labelLine: {
          show: false
        },
        data: chartsData?.is_for_benefit_breakdown ? [
          {
            value: Math.abs(parseFloat(chartsData.is_for_benefit_breakdown.for_benefit?.total || 0)),
            name: 'For Benefit',
            itemStyle: { 
              color: darkMode ? '#8b7cb8' : '#7163BA',
              shadowBlur: 10,
              shadowColor: 'rgba(113, 99, 186, 0.2)'
            }
          },
          {
            value: Math.abs(parseFloat(chartsData.is_for_benefit_breakdown.not_for_benefit?.total || 0)),
            name: 'Not For Benefit',
            itemStyle: { 
              color: darkMode ? '#c084fc' : '#800080',
              shadowBlur: 10,
              shadowColor: 'rgba(192, 132, 252, 0.2)'
            }
          }
        ] : []
      }
    ]
  };

  if (loading) {
    return (
      <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <RefreshCw className={`w-12 h-12 ${darkMode ? 'text-white' : 'text-[#7163BA]'} animate-spin mx-auto mb-4`} />
            <p className={darkMode ? 'text-white' : 'text-gray-600'}>Loading dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />
      
      <main className="flex-1 overflow-auto">
        <Header />
        
        <div className="px-8 py-8 space-y-8">
          {/* Top Header with Refresh */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Dashboard Overview</h1>
              <p className={`text-sm mt-1 ${darkMode ? 'text-gray-200' : 'text-gray-500'}`}>Track campaign finance and independent expenditures</p>
            </div>
            <button 
              onClick={handleRefresh}
              disabled={refreshing}
              className={`flex items-center gap-2 px-5 py-2.5 ${darkMode ? 'bg-[#7d6fa3] hover:bg-[#8b7cb8]' : 'bg-[#7163BA] hover:bg-[#332D54]'} text-white rounded-xl font-medium transition-all shadow-sm hover:shadow-md disabled:opacity-50`}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh Data'}
            </button>
          </div>

          {/* Stat Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {statCards.map((stat, idx) => {
              const IconComponent = stat.icon;
              const TrendIcon = stat.trend === 'up' ? TrendingUp : TrendingDown;
              
              return (
                <div key={idx} className={`${darkMode ? 'bg-[#3d3559]' : 'bg-white'} rounded-2xl p-6 border ${darkMode ? 'border-[#4a3f66]' : 'border-gray-100'} shadow-sm hover:shadow-md transition-all`}>
                  <div className="flex items-start justify-between mb-4">
                    <div 
                      className="p-3 rounded-xl" 
                      style={{ 
                        backgroundColor: darkMode ? 'rgba(139, 124, 184, 0.2)' : `${stat.color}15`,
                      }}
                    >
                      <IconComponent 
                        className="w-6 h-6" 
                        style={{ color: darkMode ? '#8b7cb8' : stat.color }}
                      />
                    </div>
                    <span className={`flex items-center gap-1 text-sm font-semibold px-2.5 py-1 rounded-full ${
                      stat.trend === 'up' 
                        ? darkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-50 text-green-700'
                        : darkMode ? 'bg-red-900/30 text-red-300' : 'bg-red-50 text-red-700'
                    }`}>
                      <TrendIcon className="w-3.5 h-3.5" />
                      {stat.change}
                    </span>
                  </div>
                  
                  <div>
                    <p className={`text-sm font-medium mb-1 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>{stat.title}</p>
                    <h3 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>{stat.value}</h3>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{stat.subtitle}</p>
                  </div>
                  
                  <button className="mt-4 text-xs font-medium flex items-center gap-1 hover:gap-2 transition-all" style={{ color: darkMode ? '#8b7cb8' : stat.color }}>
                    View Report
                    <ArrowUpRight className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Top Donors Chart */}
            <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm`}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Top 10 Donors</h3>
                  <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Highest contributors this cycle</p>
                </div>
                <button className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-gray-50'}`}>
                  <MoreVertical className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-400'}`} />
                </button>
              </div>
              
              {chartsData?.top_donors && chartsData.top_donors.length > 0 ? (
                <div className="h-80">
                  <ReactECharts 
                    option={topDonorsOption} 
                    style={{ height: '100%', width: '100%' }}
                    opts={{ renderer: 'canvas' }}
                  />
                </div>
              ) : (
                <div className={`h-80 flex items-center justify-center ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>
                  <p>No data available</p>
                </div>
              )}
            </div>

            {/* Top IE Committees Chart */}
            <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm`}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Top 10 IE Committees</h3>
                  <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Highest spending committees</p>
                </div>
                <button className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-gray-50'}`}>
                  <MoreVertical className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-400'}`} />
                </button>
              </div>
              
              {chartsData?.top_ie_committees && chartsData.top_ie_committees.length > 0 ? (
                <div className="h-80">
                  <ReactECharts 
                    option={topCommitteesOption} 
                    style={{ height: '100%', width: '100%' }}
                    opts={{ renderer: 'canvas' }}
                  />
                </div>
              ) : (
                <div className={`h-80 flex items-center justify-center ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>
                  <div className="text-center">
                    <Building2 className={`w-16 h-16 mx-auto mb-4 ${darkMode ? 'text-gray-500' : 'text-gray-300'}`} />
                    <p className={`font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>No committee data available</p>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>Check your database connection</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Row - Doughnut & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* IE Benefit Breakdown - Doughnut */}
            <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm`}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>IE Spending Type</h3>
                  <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Distribution by benefit</p>
                </div>
              </div>

              {chartsData?.is_for_benefit_breakdown &&
               chartsData.is_for_benefit_breakdown.for_benefit &&
               chartsData.is_for_benefit_breakdown.not_for_benefit &&
               (chartsData.is_for_benefit_breakdown.for_benefit.total > 0 ||
                chartsData.is_for_benefit_breakdown.not_for_benefit.total > 0) ? (
                <>
                  <div className="h-64 flex items-center justify-center">
                    <ReactECharts 
                      option={benefitBreakdownOption} 
                      style={{ height: '100%', width: '100%' }}
                      opts={{ renderer: 'canvas' }}
                    />
                  </div>
                  
                  <div className="mt-6 space-y-3">
                    <div className={`flex items-center justify-between p-3 rounded-lg ${darkMode ? 'bg-[#4a3f66]' : 'bg-purple-50'}`}>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${darkMode ? 'bg-[#8b7cb8]' : 'bg-[#7163BA]'}`}></div>
                        <span className={`text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>For Benefit</span>
                      </div>
                      <span className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {chartsData?.is_for_benefit_breakdown?.for_benefit?.percentage || 0}%
                      </span>
                    </div>
                    <div className={`flex items-center justify-between p-3 rounded-lg ${darkMode ? 'bg-[#4a3f66]' : 'bg-purple-50'}`}>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${darkMode ? 'bg-[#c084fc]' : 'bg-[#800080]'}`}></div>
                        <span className={`text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>Not For Benefit</span>
                      </div>
                      <span className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {chartsData?.is_for_benefit_breakdown?.not_for_benefit?.percentage || 0}%
                      </span>
                    </div>
                  </div>
                </>
              ) : (
                <div className={`h-64 flex items-center justify-center ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>
                  <div className="text-center">
                    <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-100'}`}>
                      <DollarSign className={`w-8 h-8 ${darkMode ? 'text-gray-500' : 'text-gray-300'}`} />
                    </div>
                    <p className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>No benefit data</p>
                  </div>
                </div>
              )}
            </div>

            {/* Recent Activity Table */}
            <div className={`lg:col-span-2 ${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm`}>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Recent Activity</h3>
                  <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Latest independent expenditures</p>
                </div>
                <button className={`flex items-center gap-2 text-sm font-medium transition-colors ${darkMode ? 'text-purple-300 hover:text-purple-200' : 'text-[#7163BA] hover:text-[#332D54]'}`}>
                  <Calendar className="w-4 h-4" />
                  Last 30 days
                </button>
              </div>

              {recentExpenditures.length > 0 ? (
                <div className="overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className={`border-b-2 ${darkMode ? 'border-[#4a3f66]' : 'border-gray-100'}`}>
                        <th className={`text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                          Committee
                        </th>
                        <th className={`text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                          Candidate
                        </th>
                        <th className={`text-center py-3 px-4 text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                          Type
                        </th>
                        <th className={`text-right py-3 px-4 text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                          Amount
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-50'}`}>
                      {recentExpenditures.slice(0, 5).map((exp, idx) => (
                        <tr key={idx} className={`transition-colors ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50'}`}>
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7163BA] to-[#332D54] flex items-center justify-center shadow-sm flex-shrink-0">
                                <span className="text-white text-xs font-semibold">
                                  {(exp.committee || 'U')[0]}
                                </span>
                              </div>
                              <div className="min-w-0">
                                <p className={`text-sm font-medium truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                                  {exp.committee || 'Unknown Committee'}
                                </p>
                                <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                                  {exp.date ? new Date(exp.date).toLocaleDateString() : 'N/A'}
                                </p>
                              </div>
                            </div>
                          </td>
                          <td className="py-4 px-4">
                            <p className={`text-sm truncate max-w-[150px] ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                              {exp.candidate || 'N/A'}
                            </p>
                          </td>
                          <td className="py-4 px-4 text-center">
                            <span className={`inline-flex px-3 py-1.5 rounded-full text-xs font-semibold ${
                              exp.is_for_benefit === true 
                                ? darkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800'
                                : exp.is_for_benefit === false
                                ? darkMode ? 'bg-red-900/30 text-red-300' : 'bg-red-100 text-red-800'
                                : darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'
                            }`}>
                              {exp.is_for_benefit === true ? 'Support' : exp.is_for_benefit === false ? 'Oppose' : 'N/A'}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-right">
                            <p className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                              ${(exp.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className={`h-64 flex items-center justify-center ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>
                  <div className="text-center">
                    <FileText className={`w-16 h-16 mx-auto mb-4 ${darkMode ? 'text-gray-500' : 'text-gray-300'}`} />
                    <p className={`font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>No recent expenditures</p>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-400'}`}>Data will appear here once available</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
