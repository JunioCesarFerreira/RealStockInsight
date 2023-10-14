import React, { useState, useEffect } from 'react';
import Graph from './components/Graph';

const App = () => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const width = 800;
  const height = 600;

  useEffect(() => {
    const apiUrl = 'http://localhost:5002/graph'; 
  
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok' + response.statusText);
        }
        return response.json();
      })
      .then(graph => {
        console.log('Data from API: ', graph); // Verifica os dados brutos
        const processedNodes = graph.nodes.map(node => ({
          id: node.id,
          label: node.label
        }));
  
        const processedLinks = graph.links.map(link => ({
          source: link.source,
          target: link.target,
          weight: link.weight
        }));
  
        console.log('Processed nodes: ', processedNodes); // Verifica os nós processados
        console.log('Processed links: ', processedLinks); // Verifica os links processados
  
        setNodes(processedNodes);
        setLinks(processedLinks);
      })
      .catch(error => console.error('Erro ao buscar dados da API:', error));
  }, []);
  
  return (
    <div className="graph-container">
      <h1>Network Graph</h1>
      <div>
      <Graph nodes={nodes} links={links} width={width} height={height} />
      </div>
    </div>
  );
};

export default App;
