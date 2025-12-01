// frontend/src/components/MoneyFlowSankey.jsx
import React, { useEffect, useState } from "react";
import { Sankey, Tooltip, ResponsiveContainer } from "recharts";
import { getMoneyFlow } from "../api/api";
import { Loader } from "lucide-react";

/**
 * Money Flow Sankey Diagram
 * Phase 1 Task 3: Visualize money flow from donors → committees → candidates
 */
export default function MoneyFlowSankey({ officeId, cycleId, limit = 20 }) {
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
      const flowData = await getMoneyFlow({ 
        office: officeId, 
        cycle: cycleId, 
        limit 
      });
      
      // Transform API data to Sankey format
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
    /**
     * Sankey expects:
     * {
     *   nodes: [{ name: "Node1" }, { name: "Node2" }],
     *   links: [{ source: 0, target: 1, value: 1000 }]
     * }
     */
    
    const nodes = [];
    const links = [];
    const nodeMap = new Map();
    
    let nodeIndex = 0;
    
    // Helper to get or create node
    const getNodeIndex = (name) => {
      if (nodeMap.has(name)) {
        return nodeMap.get(name);
      }
      const index = nodeIndex++;
      nodeMap.set(name, index);
      nodes.push({ name });
      return index;
    };
    
    // Process top donors
    if (flowData.top_donors && flowData.top_donors.length > 0) {
      flowData.top_donors.forEach((donor) => {
        const donorName = donor.entity_name || 
          `${donor.entity__first_name || ''} ${donor.entity__last_name || ''}`.trim() ||
          'Unknown Donor';
        
        const donorIndex = getNodeIndex(donorName);
        
        // Create link from donor to "IE Committees" (aggregate)
        const committeeIndex = getNodeIndex("IE Committees");
        
        links.push({
          source: donorIndex,
          target: committeeIndex,
          value: parseFloat(donor.total_contributed || 0)
        });
      });
      
      // Create links from "IE Committees" to candidates
      // For simplicity, we'll distribute the total to candidates
      const committeeIndex = getNodeIndex("IE Committees");
      
      // Get candidates from race data
      if (flowData.candidates && flowData.candidates.length > 0) {
        const totalIE = flowData.candidates.reduce((sum, c) => 
          sum + parseFloat(c.total_ie || 0), 0
        );
        
        flowData.candidates.forEach((candidate) => {
          const candidateName = candidate.candidate_name || 
            `${candidate.subject_committee__name__first_name || ''} ${candidate.subject_committee__name__last_name || ''}`.trim() ||
            'Unknown Candidate';
          
          const candidateIndex = getNodeIndex(candidateName);
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
    
    // If no data, create placeholder
    if (nodes.length === 0) {
      nodes.push({ name: "No Data Available" });
    }
    
    return { nodes, links };
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Money Flow</h3>
        <div className="flex items-center justify-center h-64">
          <Loader className="w-8 h-8 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Money Flow</h3>
        <div className="flex items-center justify-center h-64 text-red-600">
          {error}
        </div>
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Money Flow</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No money flow data available for this race
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Money Flow</h3>
        <p className="text-sm text-gray-500">
          {data.nodes.length} entities • {data.links.length} connections
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <Sankey
          data={data}
          nodeWidth={15}
          nodePadding={20}
          linkCurvature={0.5}
          iterations={32}
          node={{
            fill: "#6B5B95",
            fillOpacity: 0.8,
          }}
          link={{
            stroke: "#6B5B95",
            strokeOpacity: 0.2,
            strokeWidth: 2,
          }}
        >
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              
              const data = payload[0].payload;
              
              if (data.source !== undefined) {
                // This is a link
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                    <p className="font-semibold text-gray-900 mb-1">
                      {data.source.name} → {data.target.name}
                    </p>
                    <p className="text-sm text-gray-600">
                      ${data.value.toLocaleString()}
                    </p>
                  </div>
                );
              } else {
                // This is a node
                return (
                  <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
                    <p className="font-semibold text-gray-900">
                      {data.name}
                    </p>
                  </div>
                );
              }
            }}
          />
        </Sankey>
      </ResponsiveContainer>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-purple-600">
              {data.nodes.filter(n => !n.name.includes("Committee")).length}
            </p>
            <p className="text-xs text-gray-500">Donors</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-purple-600">
              {data.links.length}
            </p>
            <p className="text-xs text-gray-500">Transactions</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-purple-600">
              $
              {data.links.reduce((sum, l) => sum + l.value, 0).toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">Total Flow</p>
          </div>
        </div>
      </div>
    </div>
  );
}