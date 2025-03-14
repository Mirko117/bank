
$(document).ready(function() {

    // When a sidebar link is clicked, load the shell
    $("#sidebar a").on("click", function(e) {
        e.preventDefault();
        $("#sidebar a").removeClass("selected");
        this.classList.add("selected");

        // Add loading spinner
        $("#shell").html("<div class='loading'><img src='/static/images/loading.gif'></div>");

        var shell = this.getAttribute("data-shell");
        var data = { shell: shell };
        var text = this.text;

        $.ajax({
            type: "GET",
            url: "/api/admin-dashboard/get-shell",
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
        url: "/api/admin-dashboard/get-shell",
        data: { shell: "admin-dashboard" },
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

function loadShellEventListeners() {
    
    /// Admin User Transactions

    // When admin clicks search button
    $("#admin-user-transactions .actions #search-username-button").on("click", function() {
        var username = $("#admin-user-transactions .actions #search-username").val();
        var data = { username: username };

        $.ajax({
            type: "GET",
            url: "/api/admin-dashboard/get-user-transactions-table",
            data: data,
            success: function (response) {
                $("#admin-user-transactions .actions #search-transactions").removeClass("hidden");

                $("#admin-user-transactions #table").html(response.table);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });

    // When the search input is typed in, filter the transactions table
    $("#admin-user-transactions .actions #search-transactions").on("keyup", function(e){
        e.preventDefault();

        var search = $(this).val().toLowerCase();

        $("#admin-user-transactions table.transactions tbody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(search) > -1);
        });
    });
}