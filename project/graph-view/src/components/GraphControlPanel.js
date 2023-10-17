import React from 'react';

const GraphControlPanel = ({ onParamChange, visualParams, maxWeight }) => {
    return (
      <div className="control-panel">
        <table>
          <tbody>
            <tr>
              <td>Node Size:</td>
              <td>
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  value={visualParams.nodeSize}
                  onChange={(e) => onParamChange("nodeSize", e.target.value)} 
                />
              </td>
              <td>Link Distance:</td>
              <td>
                <input 
                  type="range" 
                  min="10" 
                  max="300" 
                  value={visualParams.linkDistance}
                  onChange={(e) => onParamChange("linkDistance", e.target.value)} 
                />
              </td>
              <td>Weight Threshold:</td>
              <td>
                <input 
                  type="range" 
                  min="1" 
                  max={maxWeight}
                  value={visualParams.weightThreshold}
                  onChange={(e) => onParamChange("weightThreshold", e.target.value)} 
                />
              </td>
            </tr>
            <tr>
              <td>Charge Strength:</td>
              <td>
                <input 
                  type="range" 
                  min="-100" 
                  max="10" 
                  value={visualParams.chargeStrength}
                  onChange={(e) => onParamChange("chargeStrength", e.target.value)} 
                />
              </td>
              <td>Collision Radius:</td>
              <td>
                <input 
                  type="range" 
                  min="1" 
                  max="100" 
                  value={visualParams.collisionRadius}
                  onChange={(e) => onParamChange("collisionRadius", e.target.value)} 
                />
              </td>
              <td>Center Force:</td>
              <td>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={visualParams.centerForce}
                  onChange={(e) => onParamChange("centerForce", e.target.value)} 
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
};  

export default GraphControlPanel;
