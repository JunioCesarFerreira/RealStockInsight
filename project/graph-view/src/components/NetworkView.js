import React, { useState, useEffect, useCallback } from 'react';
import Graph from './Graph';
import GraphControlPanel from './GraphControlPanel';
import * as d3 from 'd3';
import { API_BASE } from '../config';

const NetworkView = () => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState(null);
  const [visualParams, setVisualParams] = useState({
    nodeSize: 4,
    linkDistance: 200,
    chargeStrength: -10,
    collisionRadius: 50,
    weightThreshold: 2,
    centerForce: 0,
  });
  const width = 800;
  const height = 500;

  const fetchData = useCallback(() => {
    setStatus('loading');
    fetch(`${API_BASE}/graph`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
      })
      .then(graph => {
        const processedNodes = graph.nodes.map(node => ({
          id: node.id,
          label: node.label
        }));

        const processedLinks = graph.links.map(link => ({
          source: link.source,
          target: link.target,
          weight: link.weight
        }));

        setNodes(processedNodes);
        setLinks(processedLinks);
        setError(null);
        setStatus(processedNodes.length ? 'ready' : 'empty');

        const maxLinkWeight = d3.max(processedLinks, link => link.weight);
        setVisualParams(prevParams => ({ ...prevParams, maxLinkWeight }));
      })
      .catch(err => {
        console.error('Erro ao buscar dados da API:', err);
        setError(err.message);
        setStatus('error');
      });
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleParamChange = useCallback((paramName, paramValue) => {
    setVisualParams(prevParams => ({
      ...prevParams,
      [paramName]: paramValue,
    }));
  }, []);

  return (
    <div className="graph-container">
      <div className="graph-toolbar">
        <h1>Co-movement network</h1>
        <span className="graph-summary">
          {status === 'ready' && `${nodes.length} nodes · ${links.length} links`}
          {status === 'loading' && 'Loading…'}
        </span>
        <button onClick={fetchData} disabled={status === 'loading'}>Refresh</button>
      </div>
      {status === 'empty' && (
        <p className="graph-message">
          No network yet. The consumer-network builds it after the producer sends the first message —
          follow the progress on the <a href="#/monitor">Monitor</a> tab.
        </p>
      )}
      {status === 'error' && (
        <p className="graph-message graph-message-error">Could not load the network: {error}</p>
      )}
      <div>
      <Graph nodes={nodes} links={links} width={width} height={height} visualParams={visualParams} />
      <GraphControlPanel onParamChange={handleParamChange} visualParams={visualParams} maxWeight={visualParams.maxLinkWeight} />
      </div>
    </div>
  );
};

export default NetworkView;
