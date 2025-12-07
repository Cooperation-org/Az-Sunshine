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

  // Brand colors: Purple gradient (#6B5B95 to #4C3D7D)
  const nodeColor = darkMode ? '#8b7cb8' : '#6B5B95';

  return (
    <g>
      <Rectangle {...props} fill={nodeColor} fillOpacity="1"/>
      <text
        textAnchor={isOut ? "end" : "start"}
        x={isOut ? x - 6 : x + width + 6}
        y={y + height / 2}
        fontSize="13"
        fontWeight="600"
        fill={darkMode ? '#ffffff' : '#1f2937'}
        stroke={darkMode ? '#3d3559' : '#ffffff'}
        strokeWidth={3}
        strokeLinejoin="round"
        paintOrder="stroke"
      >
        {payload.name}
      </text>
    </g>
  );
};

const CustomLink = (props) => {
  const { sourceX, targetX, sourceY, targetY, sourceControlX, targetControlX, linkWidth, payload } = props;
  const { darkMode } = useDarkMode();

  // Use the color from the link data, or fall back to default purple
  const linkColor = payload.color || (darkMode ? '#8b7cb8' : '#7163BA');
  const opacity = darkMode ? 0.6 : 0.5;

  return (
    <path
      d={`
        M${sourceX},${sourceY}
        C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}
      `}
      stroke={linkColor}
      strokeWidth={linkWidth}
      fill="none"
      strokeOpacity={opacity}
      style={{ cursor: 'pointer' }}
    />
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
      const flowData = await getMoneyFlow({ office_id: officeId, cycle_id: cycleId, limit });
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
    const donorColorMap = new Map(); // Map donor index to color
    let nodeIndex = 0;

    // Color palette for different donors (distinct, vibrant colors)
    const colorPalette = [
      '#FF6B6B', // Coral Red
      '#4ECDC4', // Turquoise
      '#45B7D1', // Sky Blue
      '#FFA07A', // Light Salmon
      '#98D8C8', // Mint
      '#F7DC6F', // Yellow
      '#BB8FCE', // Purple
      '#85C1E2', // Light Blue
      '#F8B195', // Peach
      '#C06C84', // Mauve
      '#6C5B7B', // Deep Purple
      '#F67280', // Pink
    ];

    const getNodeIndex = (name, type) => {
      if (nodeMap.has(name)) {
        return nodeMap.get(name);
      }
      const index = nodeIndex++;
      nodeMap.set(name, index);
      nodes.push({ name, type });

      // Assign color to donor nodes
      if (type === 'donor') {
        const colorIndex = donorColorMap.size % colorPalette.length;
        donorColorMap.set(index, colorPalette[colorIndex]);
      }

      return index;
    };

    if (flowData.top_donors?.length > 0) {
      const committeeIndex = getNodeIndex("IE Committees", "committee");

      // Add donor -> IE Committee links (with color from donor)
      flowData.top_donors.forEach((donor) => {
        const donorName = `${donor.entity__first_name || ''} ${donor.entity__last_name || ''}`.trim() || 'Unknown Donor';
        const donorIndex = getNodeIndex(donorName, "donor");
        const donorColor = donorColorMap.get(donorIndex);

        links.push({
          source: donorIndex,
          target: committeeIndex,
          value: Math.abs(parseFloat(donor.total_contributed || 0)),
          color: donorColor, // Assign donor's color to this link
          donorIndex: donorIndex // Track which donor this came from
        });
      });

      // Add IE Committee -> Candidate links (aggregated by candidate)
      if (flowData.candidates?.length > 0) {
        const candidateMap = new Map();

        flowData.candidates.forEach((candidate) => {
          const candidateName = `${candidate.subject_committee__name__first_name || ''} ${candidate.subject_committee__name__last_name || ''}`.trim() || 'Unknown Candidate';
          const ieAmount = Math.abs(parseFloat(candidate.total_ie || 0));

          if (!candidateMap.has(candidateName)) {
            candidateMap.set(candidateName, 0);
          }
          candidateMap.set(candidateName, candidateMap.get(candidateName) + ieAmount);
        });

        candidateMap.forEach((totalAmount, candidateName) => {
          if (totalAmount > 0) {
            const candidateIndex = getNodeIndex(candidateName, "candidate");
            links.push({
              source: committeeIndex,
              target: candidateIndex,
              value: totalAmount,
              color: '#8b7cb8', // Neutral purple for aggregated committee -> candidate flows
              donorIndex: null // No specific donor (aggregated)
            });
          }
        });
      }
    }

    return { nodes, links, donorColorMap };
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

  // Convert height string to number (e.g., "400px" -> 400)
  const numericHeight = typeof height === 'string' ? parseInt(height) : height;

  return (
    <div style={{ width: '100%', height: numericHeight }}>
      <ResponsiveContainer width="100%" height={numericHeight}>
        <Sankey
          data={data}
          nodeWidth={10}
          nodePadding={15}
          linkCurvature={0.5}
          iterations={32}
          node={<CustomNode />}
          link={<CustomLink />}
        >
          <Tooltip
            cursor={{ fill: darkMode ? 'rgba(139, 124, 184, 0.2)' : 'rgba(113, 99, 186, 0.1)' }}
            content={({ active, payload }) => {
              if (!active || !payload || !payload[0]) return null;

              const item = payload[0].payload;

              // Check if this is a link (has source/target objects) or a node
              const isLink = item.source && item.target && typeof item.source === 'object';

              // Extract source and target names for links
              const sourceName = isLink ? (item.source.name || 'Unknown') : null;
              const targetName = isLink ? (item.target.name || 'Unknown') : null;
              const amount = item.value || 0;

              // Get link color for display
              const linkColor = isLink ? (item.color || '#8b7cb8') : null;
              const isDonorLink = isLink && item.donorIndex !== null;

              return (
                <div className={`p-3 rounded-lg shadow-xl border ${darkMode ? 'bg-[#332D54] border-[#4c3e7c]' : 'bg-white/95 backdrop-blur-sm border-gray-200'}`}>
                  {isLink ? (
                    // Hovering over a flow line (link)
                    <>
                      <div className="flex items-center gap-2 mb-1">
                        {isDonorLink && (
                          <div
                            className="w-3 h-3 rounded-full border border-white/30"
                            style={{ backgroundColor: linkColor }}
                          ></div>
                        )}
                        <p className={`font-semibold text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          Money Flow
                        </p>
                      </div>
                      <p className={`text-xs mb-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                        {sourceName}
                      </p>
                      <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        ↓ {isDonorLink ? 'to' : 'from'} IE Committees ↓
                      </p>
                      <p className={`text-xs mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                        {targetName}
                      </p>
                      <p className={`text-sm font-bold ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
                        ${amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </p>
                    </>
                  ) : (
                    // Hovering over a node (bar)
                    <>
                      <p className={`font-semibold text-sm mb-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {item.name || 'Unknown'}
                      </p>
                      <p className={`text-xs ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
                        Total: ${amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
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