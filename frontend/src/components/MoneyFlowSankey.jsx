// frontend/src/components/MoneyFlowSankey.jsx
import React, { useEffect, useState } from "react";
import { Sankey, Tooltip, ResponsiveContainer, Rectangle } from "recharts";
import { getMoneyFlow } from "../api/api";
import { Loader, AlertTriangle } from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";

const CustomNode = (props) => {
  const { x, y, width, height, index, payload, containerWidth } = props;
  const { darkMode } = useDarkMode();
  const isOut = x + width + 6 > containerWidth;
  return (
    <g>
      <Rectangle {...props} fill={darkMode ? '#a99eda' : '#7163BA'} fillOpacity="1"/>
      <text
        textAnchor={isOut ? "end" : "start"}
        x={isOut ? x - 6 : x + width + 6}
        y={y + height / 2}
        fontSize="12"
        fill={darkMode ? '#d1d5db' : '#374151'}
        stroke={darkMode ? '#2a2347' : '#f3f4f6'}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeOpacity={0.8}
      >
        {payload.name}
      </text>
    </g>
  );
};

export default function MoneyFlowSankey({ officeId, cycleId, limit = 12, height = '400px' }) {
  const { darkMode } = useDarkMode();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (officeId && cycleId) {
      loadMoneyFlow();
    }
  }, [officeId, cycleId, limit]);

  async function loadMoneyFlow() {
    setLoading(true);
    setError(null);
    try {
      const flowData = await getMoneyFlow({ office: officeId, cycle: cycleId, limit });
      const sankeyData = transformToSankeyData(flowData);
      setData(sankeyData);
    } catch (err) {
      console.error("Error loading money flow:", err);
      setError("Failed to load money flow data");
    } finally {
      setLoading(false);
    }
  }

  function transformToSankeyData(flowData) {
    const nodes = [];
    const links = [];
    const nodeMap = new Map();
    let nodeIndex = 0;

    const getNodeIndex = (name, type) => {
      if (nodeMap.has(name)) {
        return nodeMap.get(name);
      }
      const index = nodeIndex++;
      nodeMap.set(name, index);
      nodes.push({ name, type });
      return index;
    };

    if (flowData.top_donors?.length > 0) {
      const committeeIndex = getNodeIndex("IE Committees", "committee");
      flowData.top_donors.forEach((donor) => {
        const donorName = donor.entity_name || `${donor.entity__first_name || ''} ${donor.entity__last_name || ''}`.trim() || 'Unknown Donor';
        const donorIndex = getNodeIndex(donorName, "donor");
        links.push({
          source: donorIndex,
          target: committeeIndex,
          value: parseFloat(donor.total_contributed || 0)
        });
      });

      if (flowData.candidates?.length > 0) {
        flowData.candidates.forEach((candidate) => {
          const candidateName = candidate.candidate_name || 'Unknown Candidate';
          const candidateIndex = getNodeIndex(candidateName, "candidate");
          const ieAmount = parseFloat(candidate.total_ie || 0);
          if (ieAmount > 0) {
            links.push({
              source: committeeIndex,
              target: candidateIndex,
              value: ieAmount
            });
          }
        });
      }
    }
    
    return { nodes, links };
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <Loader className={`w-8 h-8 animate-spin ${darkMode ? 'text-purple-300' : 'text-[#7163BA]'}`} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center" style={{ height }}>
        <AlertTriangle className={`w-10 h-10 mb-2 ${darkMode ? 'text-red-400' : 'text-red-500'}`} />
        <p className={`text-sm text-center ${darkMode ? 'text-red-400' : 'text-red-600'}`}>{error}</p>
      </div>
    );
  }

  if (!data || data.links.length === 0) {
    return (
      <div className="flex items-center justify-center text-center" style={{ height }}>
        <p className={`${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>No money flow data available for this selection.</p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <Sankey
          data={data}
          nodeWidth={10}
          nodePadding={15}
          linkCurvature={0.5}
          iterations={32}
          node={<CustomNode />}
          link={{
            stroke: darkMode ? '#8b7cb8' : '#a78bfa',
            strokeOpacity: darkMode ? 0.4 : 0.3,
          }}
        >
          <Tooltip
            cursor={{ fill: darkMode ? 'rgba(139, 124, 184, 0.2)' : 'rgba(113, 99, 186, 0.1)' }}
            content={({ active, payload }) => {
              if (!active || !payload || !payload[0]) return null;
              
              const item = payload[0].payload;
              const isLink = item.sourceLinks && item.targetLinks;
              
              return (
                <div className={`p-3 rounded-lg shadow-xl border ${darkMode ? 'bg-[#332D54] border-[#4c3e7c]' : 'bg-white/95 backdrop-blur-sm border-gray-200'}`}>
                  {isLink ? (
                    <>
                      <p className={`font-semibold text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>{item.name}</p>
                      <p className={`text-xs ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
                        Total Flow: ${item.value.toLocaleString('en-US', { minimumFractionDigits: 0 })}
                      </p>
                    </>
                  ) : (
                    <>
                       <p className={`font-semibold text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {item.source.name} → {item.target.name}
                      </p>
                      <p className={`text-xs ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
                        ${item.value.toLocaleString('en-US', { minimumFractionDigits: 0 })}
                      </p>
                    </>
                  )}
                </div>
              );
            }}
          />
        </Sankey>
      </ResponsiveContainer>
    </div>
  );
}