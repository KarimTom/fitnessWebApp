const margin = { top: 40, right: 20, bottom: 50, left: 100 };
const graphWidth = 560 - (margin.left + margin.right);
const graphHeight = 400 - (margin.top + margin.bottom);
const circleRadius = 4;

const svg = d3.select('.canvas')
    .append('svg')
    .attr('width', graphWidth + margin.left + margin.right)
    .attr('height', graphHeight + margin.top + margin.bottom)

const graph = svg.append('g')
    .attr('width', graphWidth)
    .attr('height', graphHeight)
    .attr('transform', `translate(${margin.left}, ${margin.top})`);

//specifies width of x axis
const x_range = d3.scaleTime().range([0, graphWidth]);
//specifies height of y axis
const y_range = d3.scaleLinear().range([graphHeight, 0]);

const xAxisContainer = graph.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(${0}, ${graphHeight})`);

const yAxisContainer = graph.append('g')
    .attr('class', 'y-axis');

//line consist the graphs -> specifies dots (x and y coordoniates - then links them up by a line)
const line = d3.line()
    .x(function(d) {return x_range(new Date(d.date))})
    .y(function(d) {return y_range(d.value)});

const linePath = graph.append('path');

//dotted lines for more specificity when a user hovers the mouse of dots
const dottedLines = graph.append('g')
    .attr('class','lines')
    .style('opacity', 0);

//dotted lines descending to the x axis
const dottedLinesX = dottedLines.append('line')
    .attr('stroke', '#aaa')
    .attr('stroke-width', 1)
    
    
//dotted lines going to the y axis
const dottedLinesY = dottedLines.append('line')
    .attr('stroke', '#aaa')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', 4);

//combine all macros (protein/carbs/fat) and calories of the weekly user's records in one big array
var all_macros_calories = [];

data.forEach(d => {
    d.forEach(index => {
        all_macros_calories.push(index);
    });
});

console.log(all_macros_calories);

//user has pressed a button -> display the relative graph
const update = (all_macros_calories) => {

    //filter the macros/calories relative for the user (i.e., protein - get all proteins over a week from the big array)
    //                                                  (calories - get all calories over a week from the big array)
    filtered_data = all_macros_calories.filter(item => item.name == activity)
    //sort the array using date (from smallest date to largest)
    filtered_data.sort((a,b) => new Date(a.date) - new Date(b.date));

    console.log(filtered_data);
    console.log([filtered_data]);

    //domain of x and y axis
    x_range.domain(d3.extent(filtered_data, d => new Date(d.date)));
    y_range.domain([0, d3.max(filtered_data, d => d.value)]);
    
    //draw the linePath
    linePath.data([filtered_data])
        .attr('fill', 'none')
        .attr('stroke', '#00bfa5')
        .attr('stroke-width', 2)
        .attr('d', line);
        
    //circles are the dots for every day and every y (i.e., circle for day: 24/12/2021 with 100 calories of carbs)
    const circles = graph.selectAll('circle')
        .data(filtered_data);

    //draw the circle on its corresponding place
    circles.attr('r', circleRadius)
        .attr('cx', d => x_range(new Date(d.date)))
        .attr('cy', d => y_range(d.value))
        .attr('fill', '#ccc');

    circles.enter()
        .append('circle')
            .attr('r', circleRadius)
            .attr('cx', d => x_range(new Date(d.date)))
            .attr('cy', d => y_range(d.value))
            .attr('fill', '#ccc');

    //on mousehover, expand the circle to indicate
    graph.selectAll('circle')
        .on('mouseover', (d,i,n) => {
            console.log('entered mouseover');
            d3.select(n[i])
                .transition().duration(500)
                    .attr('r', circleRadius*2)
                    .attr('fill', '#fff')

            //display x and y dotted lines
            dottedLinesX
                .attr('x1', x_range(new Date(d.date)))
                .attr('x2', x_range(new Date(d.date)))
                .attr('y1', graphHeight)
                .attr('y2', y_range(d.value));

            dottedLinesY
                .attr('x1', 0)
                .attr('x2', x_range(new Date(d.date)))
                .attr('y1', y_range(d.value))
                .attr('y2', y_range(d.value));

            dottedLines.style('opacity', 1);
        })
        //revert back on mouse leave
        .on('mouseleave', (d,i,n) => {
            d3.select(n[i])
                .transition().duration(500)
                    .attr('r', circleRadius)
                    .attr('fill', '#ccc');
        
            dottedLines.style('opacity', 0);
        });
    
    //7 dates on x axis because it's a weekly
    const xAxis = d3.axisBottom(x_range)
        .ticks(7)
        .tickFormat(d3.timeFormat('%b %d'));
    const yAxis = d3.axisLeft(y_range)
        .ticks(8)
        .tickFormat(d => d + ' cal');

    xAxisContainer.call(xAxis);
    yAxisContainer.call(yAxis);

    xAxisContainer.selectAll('text')
        .attr('transform', 'rotate(-40)')
        .attr('text-anchor', 'end');
}

update(all_macros_calories);