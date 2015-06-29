function ChangeMode(state){
    if(_state != state){
        _state = state;
        grp.jQuery("#state").val(state);
        document.result_form.submit();
    } else {
        console.log("Already on state: " + state);
    }
}

function ModuleFilterChanged(){
    document.result_form.submit();
}

function TimeframeChanged(){
    document.result_form.submit();
}

lines = sapphire.widgets.lines();

function RenderActivityGraphs()
{
    if(_state != 1)
    {
        return;
    }

    d3.select('#d3-activity')
        .datum({
            title: 'Active & Inactive Users',
            metrics: [
                {
                    key: 'active',
                    title: 'Active',
                    values: _activity_data_active
                },
                {
                    key: 'inactive',
                    title: 'Inactive',
                    values: _activity_data_inactive
                }
            ]
        })
        .call(lines);

    d3.select('#d3-qa')
        .datum({
            title: 'Questions Answered',
            metrics: [
                {
                    key: 'total_answered',
                    title: 'Total Answered',
                    values: _question_data_total
                },
                {
                    key: 'correct',
                    title: 'Correct',
                    values: _question_data_correct
                },
                {
                    key: 'incorrect',
                    title: 'Incorrect',
                    values: _question_data_incorrect
                }
            ]
        })
        .call(lines);
}

grp.jQuery(document).ready(function() {
    RenderActivityGraphs();
});