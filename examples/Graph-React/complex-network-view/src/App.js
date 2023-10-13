import React, { useState, useEffect } from 'react';
import Graph from './components/Graph';

const App = () => {
  /*
  // Teste inicial sem API
  const nodes = [
    { id: 1 }, { id: 2 }, { id: 3 },
    { id: 4 }, { id: 5 }, { id: 6 },
    { id: 7 }, { id: 8 }, { id: 9 }
  ];

  const links = [
    { source: 1, target: 2 },
    { source: 2, target: 3 },
    { source: 4, target: 5 },
    { source: 5, target: 6 },
    { source: 6, target: 7 },
    { source: 6, target: 4 },
    { source: 8, target: 9 }
  ];

  // Definindo dimensões desejadas para o gráfico
  const width = 800;
  const height = 600;
  */
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const width = 800;
  const height = 600;

  useEffect(() => {
    const apiUrl = 'http://localhost:5001/graph'; 
  
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok' + response.statusText);
        }
        return response.json();
      })
      .then(data => {
        console.log('Data from API: ', data); // Verifica os dados brutos
        const processedNodes = data.graph.vertices.map(vertex => ({
          id: vertex.id,
          label: vertex.label
        }));
  
        const processedLinks = data.graph.edges.map(edge => ({
          source: edge.source,
          target: edge.target,
          weight: edge.weight
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
