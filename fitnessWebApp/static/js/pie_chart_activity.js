console.log(activities);

const pieActivity_dims = { height: 300, width: 400, radius: 150 }; 
const pieActivity_cent = { x: (pieActivity_dims.width / 2 + 5), y: (pieActivity_dims.height / 2 + 5)};
const svg_space_width = 400;
const svg_space_height = 150;
const legendRectSize = 18;                                  
const legendSpacing = 5;

const svg_placement = pieActivity_dims.width - 300

// create svg container
const svg = d3.select('.figure')
  .append('svg')
  .attr('width', pieActivity_dims.width + svg_space_width) //400
  .attr('height', pieActivity_dims.height + svg_space_height)
  .attr('transform', `translate(${svg_placement})`); 

const graphActivity = svg.append('g')
  .attr("transform", `translate(${pieActivity_cent.x}, ${pieActivity_cent.y})`);
  // translates the graphActivity group to the middle of the svg container

const pieActivity = d3.pie()
  .sort(null)
  .value(d => d.calorie_burned);
  // the value we are evaluating to create the pieActivity angles


//assigning radius and dimensions for the arcs
const arcPathActivity = d3.arc()
  .outerRadius(pieActivity_dims.radius)
  .innerRadius(pieActivity_dims.radius / 2);

const colourActivity = d3.scaleOrdinal(d3['schemeSet3'])

// join enhanced (pieActivity) data to path elements
const paths_1 = graphActivity.selectAll('path')
  .data(pieActivity(activities));

console.log(paths_1)

//draw the arc from an end angle and a start angle
const arcTweenEnterActivity = (d) => {
    var i = d3.interpolate(d.endAngle-0.1, d.startAngle);

    return function(t){
        d.startAngle = i(t);
        return arcPathActivity(d);
    }
}

paths_1.enter()
  .append('path')
    .attr('class', 'arc')
    .attr('stroke', '#fff')
    .attr('stroke-width', 3)
    .attr('fill', d => colourActivity(d.data.calorie_burned))
    //draw the arc in 1.5 seconds using arcTweenEnterActivity -> each interpolation give an end angle and a start angle to update the arc in 1.5 seconds
    .transition().duration(1500)
      .attrTween("d", arcTweenEnterActivity);

var pieActivityLegends_1 = svg.selectAll('.legend')                     
  .data(colourActivity.domain())                                   
  .enter()                                                
  .append('g')                                            
  .attr('class', 'legend')                                
  .attr('transform', function(d, i) {
    return `translate(${pieActivity_dims.width + legendSpacing}, ${i * 30})`;
  });        

pieActivityLegends_1.append('rect')                                     
  .attr('width', legendRectSize)                          
  .attr('height', legendRectSize)                         
  .style('fill', colourActivity)                                   
  .style('stroke', colourActivity);                                
          
pieActivityLegends_1.append('text')
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
 