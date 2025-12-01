// frontend/src/components/MetricCards.jsx
import React from "react";
import { DollarSign, Users, FileText, TrendingUp } from "lucide-react";

export default function MetricCards({ metrics }) {
  // metrics expected:
  // { total_ie_spending, total_candidates, total_expenditures, soi_filings, last_updated }
  if (!metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow p-6">Loading metrics…</div>
      </div>
    );
  }

  const {
    total_ie_spending = 0,
    total_candidates = 0,
    total_expenditures = 0,
    soi_filings = 0,
    last_updated = null,
  } = metrics;

  const formattedMoney = (v) => `$${Number(v || 0).toLocaleString()}`;

  const cards = [
    {
      title: "Total IE Spending",
      value: formattedMoney(total_ie_spending),
      change: "+12.3%",
      changeLabel: "+$3.14M vs last week",
      icon: DollarSign,
      iconBg: "bg-purple-100",
      iconColor: "text-[#7163BA]",
      trend: "up"
    },
    {
      title: "Candidate Committees",
      value: Number(total_candidates).toLocaleString(),
      change: "+24.6%",
      changeLabel: "+806 vs last week",
      icon: Users,
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
      trend: "up"
    },
    {
      title: "Total Expenditures",
      value: Number(total_expenditures).toLocaleString(),
      change: "+5.8%",
      changeLabel: "+249 this month",
      icon: FileText,
      iconBg: "bg-green-100",
      iconColor: "text-green-600",
      trend: "up"
    },
    {
      title: "SOI Filings",
      value: Number(soi_filings).toLocaleString(),
      change: "-8.5%",
      changeLabel: "418 uncontacted",
      icon: TrendingUp,
      iconBg: "bg-orange-100",
      iconColor: "text-orange-600",
      trend: "down"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div key={index} className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-gray-600 text-sm font-medium mb-1">{card.title}</h3>
                <div className="flex items-center gap-2">
                  <button className="w-8 h-8 bg-[#7163BA] text-white rounded-lg flex items-center justify-center hover:bg-[#332D54] transition-colors">
                    <span className="text-lg font-bold">⋮</span>
                  </button>
                </div>
              </div>
              <div className={`w-12 h-12 ${card.iconBg} rounded-xl flex items-center justify-center`}>
                <Icon className={`w-6 h-6 ${card.iconColor}`} />
              </div>
            </div>

            {/* Value */}
            <div className="mb-3">
              <div className="text-3xl font-bold text-gray-900 mb-1">{card.value}</div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-semibold ${card.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                  {card.trend === 'up' ? '↗' : '↘'} {card.change}
                </span>
                <span className="text-sm text-gray-500">{card.changeLabel}</span>
              </div>
            </div>

            {/* View Report Button */}
            <button className="w-full bg-[#7163BA] hover:bg-[#332D54] text-white py-2.5 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
              View Report
              <span>→</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}