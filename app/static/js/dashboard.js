

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
                loadShellEventListeners();
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
            loadShellEventListeners();
        },
        error: function (response) {
            showDialog(response.responseJSON.message, "Error");
        }
    });
});


function showDialog(text, title, relaod = false) {
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
        close: function(){
            if (relaod) {
                location.reload();
            }
        }
    });
}


// This function is called when a shell is loaded, and it loads the event listeners
// It's because the shell is loaded dynamically, so the event listeners need to be loaded dynamically too
function loadShellEventListeners(){

    // Clear the quick transfer input fields when the cancel button is clicked
    $("#dashboard-shell .quick-transfer .cancel").on("click", function(e) {
        e.preventDefault();
        $("#dashboard-shell .quick-transfer input.recipient").val("");
        $("#dashboard-shell .quick-transfer input.amount").val("");
    });

    // When the transfer button is clicked, send a POST request to the server
    $("#dashboard-shell .quick-transfer .transfer").on("click", function(e) {
        e.preventDefault();

        var recipient = $("#dashboard-shell .quick-transfer input.recipient").val();
        var amount = $("#dashboard-shell .quick-transfer input.amount").val();

        var data = { recipient: recipient, amount: amount };

        $.ajax({
            type: "POST",
            url: "/api/dashboard/quick-transfer",
            data: data,
            success: function (response) {
                showDialog(response.message, "Success", reload=true);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });
}

