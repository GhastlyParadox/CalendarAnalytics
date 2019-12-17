$(".diagram").html("<p>Choose calendar</p>");

// settings for date picker
$(function() {
    $( ".datepicker" ).datepicker();
    $( "#startdate" ).datepicker( "setDate", "+0d" );
    $( "#enddate" ).datepicker( "setDate", "+2w" );
});

// creates select all button
function selectAll(source) {
    checkboxes = document.getElementsByName('calendar');
    for(var i=0, n=checkboxes.length;i<n;i++) {
      checkboxes[i].checked = source.checked;
    }
    if ($('.select-all.active')[0]) {
      $('.selectable').addClass('active');
    } else {
      $('.selectable').removeClass('active');
    }
    sendFilters();
  }

// on change event for drop down date picker
$( ".datepicker" ).change(
  function () { getFilters(); }
);

// on change event for calendar buttons
$( 'input[name="radio-chart"]' ).change(
  function () { sendFilters(); }
);

// sends checkbox data to server, receives json to render chart
function sendFilters() {

  var filters = getFilters();
  $.get("/doughnut.json", filters, function(response) {
    buildDoughnut(response);
  });
}

// returns object with selected calendars and dates
function getFilters() {

  var filters = $("#selected-calendars input").serializeArray();
  var startdate = $("#startdate").val();
  var enddate = $("#enddate").val();

  filters.push({name: "startdate", value: startdate});
  filters.push({name: "enddate", value: enddate});

  return filters;
}


function buildCharts (filters) {
  var chartType = $('input[name="calendar"]:checked').val();
  var selectedCals = filters.slice(0,-2).length;
  selectedCals == 0 ? zeroCalendars(chartType) : oneCalendar(chartType);
}


function zeroCalendars(chartType) {
  $(".diagram").empty();
  $(".diagram").html("<p>Choose calendar</p>");
}

function oneCalendar(chartType) {
  sendDoughnutData();
}

// doughnut chart
function sendDoughnutData() {
  var filters = getFilters();
  $.get("/doughnut.json", filters, function(response) {
    buildDoughnut(response);
  });
}


function buildDoughnut(response) {
  var durations = response['durations'];
  var labels = response['labels'];
  var colors = response['colors'];
  $(".diagram").empty();
  $(".diagram").html('<canvas id="pieChart" width="550" height="500"></canvas>');
  var selectedName = $(".active input").val();
  $('.diagram').prepend('<h4 class="name">'+ selectedName + '</h4>');

  doughnutSettings(durations, labels, colors);
}

var chartRendered = false;                    //for download()

function doughnutSettings(durations, labels, colors) {

  function roundHalf(num) {
    return Math.round(num*2)/2;
  }

  var myChart = new Chart(document.getElementById("pieChart"), {
    type: 'doughnut',
    data: {
      datasets: [{
        data: durations,
            backgroundColor: colors,
            hoverBackgroundColor: colors}],
        labels: labels},
    options: {
      animation: {                                    //required for download()
        onComplete: function() {
          chartRendered = true
        }
      },
      pieceLabel: {
        render: 'percentage',
        precision: 1,
        position: 'outside',
        fontStyle: 'bold',
        fontSize: 13,
        segment: true,
        segmentColor: 'auto'
      },
      legend: {
        display: true,
        position: 'bottom',
        legendCallback: function(chart) {
             var legendHtml = [];
             legendHtml.push('<ul style="padding: 15%"');
             for (var i = 0; i < chart.data.datasets.length; i++) {
               legendHtml.push('<li>');
               legendHtml.push('<span style="background-color:' + chart.data.datasets[i].borderColor + '">' + chart.data.datasets[i].color + '</span>');
               legendHtml.push('</li>');
             }
             legendHtml.push('</ul>');
             return legendHtml.join("");
        }
      },
      tooltips: {
          callbacks: {
            label: function(tooltipItem, data) {
              return roundHalf(Math.round(data['datasets'][0]['data'][tooltipItem['index']]) / 60).toFixed(1) + " hours";
            }
          },
          backgroundColor: '#303b4c',
          titleFontSize: 16,
          titleFontColor: '#0066ff',
          bodyFontColor: '#f0f8ff',
          bodyFontSize: 14,
          displayColors: false,
        },

       }
     });
}

function download() {                                             //Creates link to download the chart as a .jpeg
  if (!chartRendered) return; // return if chart not rendered
  html2canvas(document.getElementById('pieChart'), {
    onrendered: function(canvas) {
      var link = document.createElement('a');
      link.href = canvas.toDataURL('image/jpeg');
      link.download = 'myChart.jpeg';
      link.click();
    }
  })
}
