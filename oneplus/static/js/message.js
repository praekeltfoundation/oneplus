function loadCourses()
{
    var url = "/courses";
    $.getJSON(url, function(data) {
        $('#id_course').empty();
        if (data.length != 0)
        {
            $('#id_course').append(new Option('All', 'all'))
            $.each(data, function() {
                $('#id_course').append(new Option(this.name, this.id));
            });
        }
        else
        {
            loadClasses('null');
        }
    });
}

function loadClasses(course)
{
    var url = "/classes/" + course;
    $.getJSON(url, function(data) {
        $('#id_to_class').empty();
        if (data.length != 0)
        {
            $('#id_to_class').append(new Option('All Classes', 'all'));
            $.each(data, function() {
                $('#id_to_class').append(new Option(this.name, this.id));
            });
        }
        else
        {
            loadUsers('null');
        }
    });
}

function loadUsers(classs)
{
    var url = "/users/" + classs;
    $.getJSON(url, function(data) {
        $('#id_users').empty();
        if (data.length != 0)
        {
            $('#id_users').append(new Option('All', 'all'))
            $.each(data, function() {
                $('#id_users').append(new Option(this.name, this.id));
            });
        }
    });
}

$(document).ready(
    function() {
        loadCourses();
        loadClasses('all');
        loadUsers('all');

        //on course change load correct classes
        $('#id_course').on('change', function() {
            loadClasses($("#id_course option:selected").val());
        });

        //on class change load correct users
        $('#id_to_class').on('change', function(){
            loadUsers($("#id_to_class option:selected").val());
        });
    });