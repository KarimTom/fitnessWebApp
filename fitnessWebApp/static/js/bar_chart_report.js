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

const x = d3.scaleTime().range([0, graphWidth]);
const y = d3.scaleLinear().range([graphHeight, 0]);

const xAxisGroup = graph.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(${0}, ${graphHeight})`);

const yAxisGroup = graph.append('g')
    .attr('class', 'y-axis');

const line = d3.line()
    .x(function(d) {return x(new Date(d.date))})
    .y(function(d) {return y(d.value)});

const path = graph.append('path');

const dottedLines = graph.append('g')
    .attr('class','lines')
    .style('opacity', 0);

const xDottedLine = dottedLines.append('line')
    .attr('stroke', '#aaa')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', 4);

const yDottedLine = dottedLines.append('line')
    .attr('stroke', '#aaa')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', 4);

var array_data = [];

data.forEach(d => {
    d.forEach(index => {
        array_data.push(index);
    });
});

console.log(array_data);

const update = (array_data) => {

    filtered_data = array_data.filter(item => item.name == activity)
    filtered_data.sort((a,b) => new Date(a.date) - new Date(b.date));

    console.log(filtered_data);
    console.log([filtered_data]);

    x.domain(d3.extent(filtered_data, d => new Date(d.date)));
    y.domain([0, d3.max(filtered_data, d => d.value)]);
    
    path.data([filtered_data])
        .attr('fill', 'none')
        .attr('stroke', '#00bfa5')
        .attr('stroke-width', 2)
        .attr('d', line);
        
    const circles = graph.selectAll('circle')
        .data(filtered_data);

    circles.attr('r', circleRadius)
        .attr('cx', d => x(new Date(d.date)))
        .attr('cy', d => y(d.value))
        .attr('fill', '#ccc');

    circles.enter()
        .append('circle')
            .attr('r', circleRadius)
            .attr('cx', d => x(new Date(d.date)))
            .attr('cy', d => y(d.value))
            .attr('fill', '#ccc');

    graph.selectAll('circle')
        .on('mouseover', (d,i,n) => {
            console.log('entered mouseover');
            d3.select(n[i])
                .transition().duration(500)
                    .attr('r', circleRadius*2)
                    .attr('fill', '#fff')

            xDottedLine
                .attr('x1', x(new Date(d.date)))
                .attr('x2', x(new Date(d.date)))
                .attr('y1', graphHeight)
                .attr('y2', y(d.value));

            yDottedLine
                .attr('x1', 0)
                .attr('x2', x(new Date(d.date)))
                .attr('y1', y(d.value))
                .attr('y2', y(d.value));

            dottedLines.style('opacity', 1);
        })
        .on('mouseleave', (d,i,n) => {
            d3.select(n[i])
                .transition().duration(500)
                    .attr('r', circleRadius)
                    .attr('fill', '#ccc');
        
            dottedLines.style('opacity', 0);
        });
        
    const xAxis = d3.axisBottom(x)
        .ticks(7)
        .tickFormat(d3.timeFormat('%b %d'));
    const yAxis = d3.axisLeft(y)
        .ticks(8)
        .tickFormat(d => d + ' cal');

    xAxisGroup.call(xAxis);
    yAxisGroup.call(yAxis);

    xAxisGroup.selectAll('text')
        .attr('transform', 'rotate(-40)')
        .attr('text-anchor', 'end');
}

update(array_data);