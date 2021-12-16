console.log(macros);

const pieCalories_dims = { height: 300, width: 400, radius: 150 }; 
const pieCalories_cent = { x: (pieCalories_dims.width / 2 + 5), y: (pieCalories_dims.height / 2 + 5)};
const svg_space_width = 100;
const svg_space_height = 150;
const legendRectSize = 18;                                  
const legendSpacing = 5;

// create svg container
const svg = d3.select('.canvas')
  .append('svg')
  .attr('width', pieCalories_dims.width + svg_space_width)
  .attr('height', pieCalories_dims.height + svg_space_height);

const graphCalories = svg.append('g')
  .attr("transform", `translate(${pieCalories_cent.x}, ${pieCalories_cent.y})`);
  // translates the graphCalories group to the middle of the svg container

const pieCalories = d3.pie()
  .sort(null)
  .value(d => (d.value + 1));
  // the value we are evaluating to create the pieCalories angles


//assigning radius and dimensions for the arcs
const arcPath = d3.arc()
  .outerRadius(pieCalories_dims.radius)
  .innerRadius(pieCalories_dims.radius / 2);

const colour = d3.scaleOrdinal(d3['schemeSet3'])

  // join enhanced (pieCalories) data to path elements
const paths = graphCalories.selectAll('path')
  .data(pieCalories(macros));


//draw the arc from an end angle and a start angle
const arcTweenEnterCalories = (d) => {
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
     //draw the arc in 1.5 seconds using arcTweenEnterCalories -> each interpolation give an end angle and a start angle to update the arc in 1.5 seconds
    .transition().duration(1500)
      .attrTween("d", arcTweenEnterCalories);

console.log(svg);

var pieCaloriesLegends = svg.selectAll('.legend')                     
  .data(colour.domain())                                   
  .enter()                                                
  .append('g')                                            
  .attr('class', 'legend')                                
  .attr('transform', function(d, i) {
    return `translate(${pieCalories_dims.width - (6 * legendSpacing)}, ${i * 30})`;
  });        
                            
pieCaloriesLegends.append('rect')                                     
  .attr('width', legendRectSize)                          
  .attr('height', legendRectSize)                         
  .style('fill', colour)                                   
  .style('stroke', colour);                                
          
pieCaloriesLegends.append('text')                                     
  .attr('x', legendRectSize + legendSpacing)              
  .attr('y', legendRectSize - legendSpacing)              
  .text(function(d) { 
    var nutrientInfo = macros.filter(a => a.name === d);
    return (nutrientInfo[0].value + " " + nutrientInfo[0].name);
  })
  .attr('fill', '#ccc'); 



