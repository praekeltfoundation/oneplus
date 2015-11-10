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

    $.getJSON('/report_sumit_list/',
        function(data){
            s = $('#sumit_report_param');
            $.each(data, function(i, row){
                s.append($('<option>',{
                    value: row.id,
                    text: row.name
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


function getSumitReportUrl(mode){
    sumit = $('#sumit_report_param option:selected').val();
    return '/report_sumit_report/' + mode + '/' + sumit;
}

$('#learner_report_csv').click(function(){
    document.location.href=getLearnerReportUrl(1);
    return false;
});

$('#learner_report_xls').click(function(){
    document.location.href=getLearnerReportUrl(2);
    return false;
});

$('#sumit_report_csv').click(function(){
    document.location.href=getSumitReportUrl(1);
    return false;
})

$('#sumit_report_xls').click(function(){
    document.location.href=getSumitReportUrl(2);
    return false;
})

getData();