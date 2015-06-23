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