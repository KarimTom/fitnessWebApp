console.log(macros);

const pie_dims = { height: 300, width: 400, radius: 150 }; 
const pie_cent = { x: (pie_dims.width / 2 + 5), y: (pie_dims.height / 2 + 5)};
const svg_space_width = 100;
const svg_space_height = 150;
const legendRectSize = 18;                                  
const legendSpacing = 5;

// create svg container
const svg = d3.select('.canvas')
  .append('svg')
  .attr('width', pie_dims.width + svg_space_width)
  .attr('height', pie_dims.height + svg_space_height);

const graph = svg.append('g')
  .attr("transform", `translate(${pie_cent.x}, ${pie_cent.y})`);
  // translates the graph group to the middle of the svg container

const pie = d3.pie()
  .sort(null)
  .value(d => (d.value + 1));
  // the value we are evaluating to create the pie angles

const arcPath = d3.arc()
  .outerRadius(pie_dims.radius)
  .innerRadius(pie_dims.radius / 2);

const colour = d3.scaleOrdinal(d3['schemeSet3'])

  // join enhanced (pie) data to path elements
const paths = graph.selectAll('path')
  .data(pie(macros));


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

console.log(svg);

var pie_legends = svg.selectAll('.legend')                     
  .data(colour.domain())                                   
  .enter()                                                
  .append('g')                                            
  .attr('class', 'legend')                                
  .attr('transform', function(d, i) {
    return `translate(${pie_dims.width - (6 * legendSpacing)}, ${i * 30})`;
  });        
                            
pie_legends.append('rect')                                     
  .attr('width', legendRectSize)                          
  .attr('height', legendRectSize)                         
  .style('fill', colour)                                   
  .style('stroke', colour);                                
          
pie_legends.append('text')                                     
  .attr('x', legendRectSize + legendSpacing)              
  .attr('y', legendRectSize - legendSpacing)              
  .text(function(d) { 
    var nutrientInfo = macros.filter(a => a.name === d);
    return (nutrientInfo[0].value + " " + nutrientInfo[0].name);
  })
  .attr('fill', '#ccc'); 



