const bar_placement = { y: 75, x: 0};
const bar_height = 250;
//2 JSON -> one with name of calorie goal and other is for calories consumed
const calorie_goal = calories.filter(a => a.name === 'calorie goal');
//Scale the height of the bar from 0 to 250
const scaler = d3.scaleLinear()
  .domain([0, calorie_goal[0].value])
  .range([250, 0]);
const svg_width = 300;
const svg_height = 500;

const svg_1 = d3.select('.canvas-bar')
  .append('svg')
  .attr('width', svg_width)
  .attr('height', svg_height);

const rects = svg_1.append('g')
  .attr('transform', `translate(${bar_placement.x}, ${bar_placement.y})`); 
  
const cals = rects.selectAll('rect')
  .data(calories);

//shape of the bars
//height starts from 250 to calorie goal - d (d one time is calorie goal -> 0; and other is calorie consumed -> 250 - x)
cals.enter()
  .append('rect')
  .attr('width', 10)
  .attr('height', 0)
  .attr('fill', d => d.filler)
  .attr('y', bar_height)
  .transition().duration(1500)
    .attr('y', d => scaler(d.value))
    .attr('height', d => scaler(calorie_goal[0].value - d.value))
    
/*names = [];
for (let i = 0; i < calories.length; i++){
    names.push(calories[i].name);
}*/

const legend = svg_1.append('g')
    .attr('transform', `translate(${bar_placement.x + 5})`);

//legends in shape of squares (rect with same width and height)
const rect_legends = legend.selectAll('rect')
    .data(calories);

//legends placements
rect_legends.enter()
    .append('rect')
    .attr('x', 20)
    .attr('y', (d, i) => (bar_placement.y) + (i * 30))
    .attr('width', legendRectSize)
    .attr('height', legendRectSize)
    .attr('fill', d => d.filler);

//legends texts
const text_legends = legend.selectAll('text')
    .data(calories);

//texts placements
text_legends.enter()
    .append('text')
    .attr('x', 40)
    .attr('y', (d, i) => (bar_placement.y + 10) + (i * 30))
    .attr('dy', ".35em")
    .text(function(d) {
        var calorieInfo = calories.filter(a => a.name === d.name);
        return (calorieInfo[0].value + " " + calorieInfo[0].name);
    })
    .attr('fill', d => d.filler);


