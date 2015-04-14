var pie = sapphire.widgets.pie()
  .key(function(d) { return d.key; })
  .colors(d3.scale.category20());

var lines = sapphire.widgets.lines()
    .yMax(100)
    .yFormat(d3.format(',%'));

var dt = new Date().getTime()

function getData(){
    $.getJSON('/dashboard_data',
        function(data){
            d3.select('#reg')
                .datum({
                    title: 'Registrations',
                    metrics: [{
                        key: 'Registrations Last 24h',
                        title: 'Last 24h',
                        value: data.num_learn_reg_24
                    },
                    {
                        key: 'Registrations Last 48h',
                        title: 'Last 48h',
                        value: data.num_learn_reg_48
                    },
                    {
                        key: 'Registrations Last 168h',
                        title: 'Last 168h',
                        value: data.num_learn_reg_168
                    },
                    {
                        key: 'Registrations Last 744h',
                        title: 'Last 744h',
                        value: data.num_learn_reg_744
                    }]
                })
                .call(pie);

            d3.select('#act')
                .datum({
                    title: 'Active Users',
                    metrics: [{
                        key: 'Active Last 24h',
                        title: 'Last 24h',
                        value: data.num_learn_act_24
                    },
                    {
                        key: 'Active Last 48h',
                        title: 'Last 48h',
                        value: data.num_learn_act_48
                    },
                    {
                        key: 'Active Last 168h',
                        title: 'Last 168h',
                        value: data.num_learn_act_168
                    },
                    {
                        key: 'Active Last 744h',
                        title: 'Last 744h',
                        value: data.num_learn_act_744
                    }]
                })
                .call(pie);

            d3.select('#q_ans_24')
                .datum({
                    title: ' Questions Answered Last 24h',
                    metrics: [{
                        key: 'Incorrect Last 24h',
                        title: 'Incorrect',
                        value: data.num_q_ans_24 - data.num_q_ans_cor_48
                    },
                    {
                        key: 'Correct Last 24h',
                        title: 'Correct',
                        value: data.num_q_ans_cor_24
                    }]
                })
                .call(pie);

            d3.select('#q_ans_48')
                .datum({
                    title: ' Questions Answered Last 48h',
                    metrics: [{
                        key: 'Incorrect Last 48h',
                        title: 'Incorrect',
                        value: data.num_q_ans_48 - data.num_q_ans_cor_48
                    },
                    {
                        key: 'Correct Last 48h',
                        title: 'Correct',
                        value: data.num_q_ans_cor_48
                    }]
                })
                .call(pie);

            d3.select('#q_ans_168')
                .datum({
                    title: ' Questions Answered Last 168h',
                    metrics: [{
                        key: 'Incorrect Last 168h',
                        title: 'Incorrect',
                        value: data.num_q_ans_168 - data.num_q_ans_cor_168
                    },
                    {
                        key: 'Correct Last 168h',
                        title: 'Correct',
                        value: data.num_q_ans_cor_168
                    }]
                })
                .call(pie);

            d3.select('#optin_sms')
                .datum({
                    title: 'SMS Optin Status',
                    metrics: [{
                        key: 'SMS Not Optins',
                        title: 'SMS Not Optins',
                        value: data.tot_learners - data.num_sms_optin
                    },
                    {
                        key: 'SMS Optins',
                        title: 'SMS Optins',
                        value: data.num_sms_optin
                    }]
                })
                .call(pie);

            d3.select('#optin_email')
                .datum({
                    title: 'Email Optin Status',
                    metrics: [{
                        key: 'Email Not Optins',
                        title: 'Email Not Optins',
                        value: data.tot_learners - data.num_email_optin
                    },
                    {
                        key: 'Email Optins',
                        title: 'Email Optins',
                        value: data.num_email_optin
                    }]
                })
                .call(pie);
        });
}

getData();