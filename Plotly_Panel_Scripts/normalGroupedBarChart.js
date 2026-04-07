// Build traces from Grafana data
const traces = data.series.map((s) => {
  const xVals = Array.from(s.fields[0].values);   // timestamps in ms
  const yVals = Array.from(s.fields[1].values);   // numeric values

  return {
    type: 'bar',
    name: s.name,
    x: xVals,
    y: yVals
  };
});

// Layout settings
const layout = {
  title: 'Planned Vs Forced Outages',
  barmode: 'group',   // change to 'stack' if you want stacked bars
  bargap: 0.45,         // ⬅ thinner bars
  bargroupgap: 0.25 ,    // ⬅ thinner bars inside each group
  xaxis: {
    type: 'date',
    title: '',
    tickformat: '%d-%b',      // 11-Jan style
    hoverformat: '%d-%b',     // tooltip also 11-Jan
    tickangle: -30 ,    
    tickmode: 'linear',   
    tick0: traces[0].x[0] 
  },

  yaxis: {
    title: '',
  },

  // Legend styling
  legend: {
    orientation: 'h',     // horizontal row
    font: { size: 10 },    // smaller font
    x: 0,                  // bottom-left
    y: -0.2,               // position below the plot (south)
    xanchor: 'left',
    yanchor: 'top'
  },
};

// Return result to Plotly panel
return {
  data: traces,
  layout: layout
};
