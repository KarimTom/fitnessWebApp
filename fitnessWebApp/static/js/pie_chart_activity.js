console.log(activities);

const pie_dims = { height: 300, width: 400, radius: 150 }; 
const pie_cent = { x: (pie_dims.width / 2 + 5), y: (pie_dims.height / 2 + 5)};
const svg_space_width = 350;
const svg_space_height = 150;
const legendRectSize = 18;                                  
const legendSpacing = 5;

const svg_placement = pie_dims.width - 300

// create svg container
const svg = d3.select('.figure')
  .append('svg')
  .attr('width', pie_dims.width + svg_space_width) //400
  .attr('height', pie_dims.height + svg_space_height)
  .attr('transform', `translate(${svg_placement})`); 

const graph_1 = svg.append('g')
  .attr("transform", `translate(${pie_cent.x}, ${pie_cent.y})`);
  // translates the graph_1 group to the middle of the svg container

const pie_1 = d3.pie()
  .sort(null)
  .value(d => d.calorie_burned);
  // the value we are evaluating to create the pie_1 angles

const arcPath_1 = d3.arc()
  .outerRadius(pie_dims.radius)
  .innerRadius(pie_dims.radius / 2);

const colour_1 = d3.scaleOrdinal(d3['schemeSet3'])

// join enhanced (pie) data to path elements
const paths_1 = graph_1.selectAll('path')
  .data(pie_1(activities));

console.log(paths_1)

const arcTweenEnter_1 = (d) => {
    var i = d3.interpolate(d.endAngle-0.1, d.startAngle);

    return function(t){
        d.startAngle = i(t);
        return arcPath_1(d);
    }
}

paths_1.enter()
  .append('path')
    .attr('class', 'arc')
    .attr('stroke', '#fff')
    .attr('stroke-width', 3)
    .attr('fill', d => colour_1(d.data.calorie_burned))
    .transition().duration(1500)
      .attrTween("d", arcTweenEnter_1);

var pieLegends_1 = svg.selectAll('.legend')                     
  .data(colour_1.domain())                                   
  .enter()                                                
  .append('g')                                            
  .attr('class', 'legend')                                
  .attr('transform', function(d, i) {
    return `translate(${pie_dims.width + legendSpacing}, ${i * 30})`;
  });        

pieLegends_1.append('rect')                                     
  .attr('width', legendRectSize)                          
  .attr('height', legendRectSize)                         
  .style('fill', colour_1)                                   
  .style('stroke', colour_1);                                
          
pieLegends_1.append('text')
    .attr('x', legendRectSize + legendSpacing)              
    .attr('y', legendRectSize - legendSpacing)              
    .text(function(d) {
    console.log(d); 
    var activityInfo = activities.filter(a => a.calorie_burned === d);
    console.log(activityInfo);
    return (activityInfo[0].calorie_burned + " " + activityInfo[0].unit + 
            ", " + activityInfo[0].name + ", " + activityInfo[0].duration + " min");
    })
    .attr('fill', '#ccc');                                    
 