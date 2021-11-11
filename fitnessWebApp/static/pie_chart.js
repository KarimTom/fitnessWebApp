console.log(data);
const dims = { height: 300, width: 300, radius: 150 };
const cent = { x: (dims.width / 2 + 5), y: (dims.height / 2 + 5)};
const legendRectSize = 18;                                  
const legendSpacing = 4;

// create svg container
const svg = d3.select('.canvas')
  .append('svg')
  .attr('width', dims.width + 150)
  .attr('height', dims.height + 150);

const graph = svg.append('g')
  .attr("transform", `translate(${cent.x}, ${cent.y})`);
  // translates the graph group to the middle of the svg container

const pie = d3.pie()
  .sort(null)
  .value(d => (d.value + 1));
  // the value we are evaluating to create the pie angles

const arcPath = d3.arc()
  .outerRadius(dims.radius)
  .innerRadius(dims.radius / 2);

const colour = d3.scaleOrdinal(d3['schemeSet3'])

  // join enhanced (pie) data to path elements
const paths = graph.selectAll('path')
  .data(pie(data));


const arcTweenEnter = (d) => {
    var i = d3.interpolate(d.endAngle-0.1, d.startAngle);

    return function(t){
        d.startAngle = i(t);
        return arcPath(d);
    }
}

paths.enter()
  .append('path')
    .attr('class', 'arc')
    .attr('stroke', '#fff')
    .attr('stroke-width', 3)
    .attr('fill', d => colour(d.data.name))
    .transition().duration(1500)
      .attrTween("d", arcTweenEnter);

var legend = svg.selectAll('.legend')                     
  .data(colour.domain())                                   
  .enter()                                                
  .append('g')                                            
  .attr('class', 'legend')                                
  .attr('transform', function(d, i) {
    console.log(d)
    return `translate(${dims.width + 5}, ${i * 30})`;
  });        
                            
legend.append('rect')                                     
  .attr('width', legendRectSize)                          
  .attr('height', legendRectSize)                         
  .style('fill', colour)                                   
  .style('stroke', colour);                                
          
legend.append('text')                                     
  .attr('x', legendRectSize + legendSpacing)              
  .attr('y', legendRectSize - legendSpacing)              
  .text(function(d) { 
    var nutrientInfo = data.filter(a => a.name === d);
    return (nutrientInfo[0].value + " " + nutrientInfo[0].name);
  }); 
