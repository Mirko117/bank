

$(document).ready(function() {

    // When a sidebar link is clicked, load the shell
    $("#sidebar a").on("click", function(e) {
        e.preventDefault();
        $("#sidebar a").removeClass("selected");
        this.classList.add("selected");

        var shell = this.getAttribute("data-shell");
        var data = { shell: shell };
        var text = this.text;

        $.ajax({
            type: "GET",
            url: "/api/dashboard/get-shell",
            data: data,
            success: function (response) {
                $("#shell").html(response.shell);
                $("#navbar .page-name").text(text);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });

    // When the page loads, load the dashboard shell
    $.ajax({
        type: "GET",
        url: "/api/dashboard/get-shell",
        data: { shell: "dashboard" },
        success: function (response) {
            $("#shell").html(response.shell);
        },
        error: function (response) {
            showDialog(response.responseJSON.message, "Error");
        }
    });
});


function showDialog(text, title){
    $("<div>" + text + "</div>").dialog({
        title: title,
        modal: true,
        resizable: false,
        draggable: false,
        position: { my: "top+100", at: "top", of: window },
        buttons: {
            Ok: function(){
                $(this).dialog('close');
                return true;
            }
        },
    });
}