import React, { useRef, useEffect } from 'react';
import './Graph.css';
import * as d3 from 'd3';

const Graph = ({ nodes, links, width, height }) => {
  const svgRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);

    const simulation = d3.forceSimulation(nodes)
      .alphaDecay(0.01)
      .force("link", d3.forceLink(links).id(d => d.id).distance(50))
      .force("charge", d3.forceManyBody().strength(-10))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(10));

    // Criação dos nós e arestas usando D3.js
    const link = svg
      .selectAll(".link")
      .data(links)
      .enter()
      .append("line")
      .attr("class", "link");

    const node = svg
      .selectAll(".node")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("class", "node")
      .attr("r", 5);

    // Adicionando labels aos vértices
    svg.selectAll(".node-label")
        .data(nodes)
        .join("text")
        .attr("class", "node-label")
        .attr("x", d => d.x)
        .attr("y", d => d.y)
        .text(d => d.label)
        .attr("dy", "-1em");

    // Adicionando labels às arestas
    svg.selectAll(".link-label")
        .data(links)
        .join("text")
        .attr("class", "link-label")
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2)
        .text(d => d.weight.toString())
        .attr("dy", "-0.5em");
    
    // Funções de arrastar
    const dragStart = (event, d) => {
      if (!event.active) simulation.alphaDecay(0.01).restart();
      d.fx = d.x;
      d.fy = d.y;
    };
  
    const dragged = (event, d) => {
      d.fx = event.x;
      d.fy = event.y;
    };
  
    const dragEnd = (event, d) => {
      if (!event.active) simulation.alphaTarget(0.01);
      d.fx = null;
      d.fy = null;
    };
  
    // Aplicando o drag aos nós
    const drag = d3.drag()
      .on("start", dragStart)
      .on("drag", dragged)
      .on("end", dragEnd);
  
    node.call(drag);
  
    // Atualização da posição dos nós e arestas durante a simulação
    simulation.on("tick", () => {
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);
    
        node
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
          
        // Atualize a posição dos rótulos dos nós
        svg.selectAll(".node-label")
          .attr("x", d => d.x)
          .attr("y", d => d.y);
        
        // Atualize a posição dos rótulos das arestas
        svg.selectAll(".link-label")
          .attr("x", d => (d.source.x + d.target.x) / 2)
          .attr("y", d => (d.source.y + d.target.y) / 2);
    });
  }, [nodes, links, width, height]);

  return (
    <svg ref={svgRef} width={width} height={height}></svg>
  );
};

export default Graph;
