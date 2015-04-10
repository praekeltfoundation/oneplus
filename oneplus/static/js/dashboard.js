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

            d3.select('#q_ans')
                .datum({
                    title: 'Number of Questions Answered',
                    metrics: [{
                        key: 'Questions Answered Last 24h',
                        title: 'Last 24h',
                        value: data.num_q_ans_24
                    },
                    {
                        key: 'Questions Answered Last 48h',
                        title: 'Last 48h',
                        value: data.num_q_ans_48
                    },
                    {
                        key: 'Questions Answered Last 168h',
                        title: 'Last 168h',
                        value: data.num_q_ans_168
                    }]
                })
                .call(pie);

            /*d3.select('#q_ans_c')
                .datum({
                    title: 'Percentage of Questions Answered Correct',
                    metrics: [{
                        key: 'Questions Answered Correct Last 24h',
                        title: 'Last 24h',
                        value: data.prc_q_ans_cor_24
                    },
                    {
                        key: 'Questions Answered Correct Last 48h',
                        title: 'Last 48h',
                        value: data.prc_q_ans_cor_48
                    },
                    {
                        key: 'Questions Answered Correct Last 168h',
                        title: 'Last 168h',
                        value: data.prc_q_ans_cor_168
                    }]
                })
                .call(pie);*/

            d3.select('#q_ans_c')
                .datum({
                    key: 'Percentage of Questions Answered Correct',
                    title: 'Percentage of Questions Answered Correct',
                    metrics: [
                        {
                            key: 'Questions Answered Correct Last 24h',
                            title: 'Last 24h',
                            values: [{
                                x: dt,
                                y: data.prc_q_ans_cor_24
                            }]
                        },
                        {
                            key: 'Questions Answered Correct Last 48h',
                            title: 'Last 48h',
                            values: [{
                                x: dt,
                                y: data.prc_q_ans_cor_48
                            }]
                        },
                        {
                            key: 'Questions Answered Correct Last 168h',
                            title: 'Last 168h',
                            values: [{
                                x: dt,
                                y: data.prc_q_ans_cor_168
                            }]
                        }]
                })
                .call(lines);

            /*d3.select('#optin')
                .datum({
                    title: 'Optin Percentages',
                    metrics: [{
                        key: 'SMS Optins',
                        title: 'SMS',
                        value: data.prc_sms_optin
                    },
                    {
                        key: 'e-mail Optins',
                        title: 'e-mail',
                        value: data.prc_email_optin
                    }]
                })
                .call(pie);*/

            d3.select('#optin')
                .datum({
                    title: 'Optin Percentages',
                    key: 'a',
                    metrics: [
                        {
                            key: 'sms_optins',
                            title: 'SMS',
                            values: [{
                                x: dt,
                                y: data.prc_sms_optin
                            }]
                        },
                        {
                            key: 'e-mail_optins',
                            title: 'e-mail',
                            values: [{
                                x: dt,
                                y: data.prc_email_optin
                            }]
                        }
                    ]
                })
                .call(lines);
        });
}


getData();