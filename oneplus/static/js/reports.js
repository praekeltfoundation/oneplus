function getData(){
    $.getJSON('/reports_learner_unique_regions',
        function(data){
            s = $('#learner_report_param');
            s.append('<option>All</option>')
            $.each(data, function(i, row){
                s.append($('<option>',{
                    value: null,
                    text: row.area
                }));
            });
        });
}

function getLearnerReportUrl(mode){
    region = $('#learner_report_param option:selected').text();
    if(region == 'All'){
        region = '';
    }

    return '/report_learner_report/' + mode + '/' + region;
}

$('#learner_report_csv').click(function(){
    document.location.href=getLearnerReportUrl(1);
    return false;
});

$('#learner_report_xls').click(function(){
    document.location.href=getLearnerReportUrl(2);
    return false;
});

getData();