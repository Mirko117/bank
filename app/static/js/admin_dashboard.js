
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

    // When the page loads, load the transfers shell
    $.ajax({
        type: "GET",
        url: "/api/admin-dashboard/get-shell",
        data: { shell: "admin-transfers" },
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

    /// Admin Transfers Shell

    // Currency input listener
    $("#admin-transfers-shell .transfer-details #currency").on("change", function(e){
        e.preventDefault();
        handleTransferSumarry();
    });

    // Amount input listener
    $("#admin-transfers-shell .transfer-details #amount").on("change", function(e){
        e.preventDefault();
        handleTransferSumarry();
    });

    // Recipient input listener
    $("#admin-transfers-shell .transfer-details #recipient").on("change", function(e){
        e.preventDefault();
        handleTransferSumarry();
    });

    // Handle transfer summary when user inputs data
    function handleTransferSumarry(){
        var currency = $("#admin-transfers-shell .transfer-details #currency").val();
        var amount = $("#admin-transfers-shell .transfer-details #amount").val();
        var recipient = $("#admin-transfers-shell .transfer-details #recipient").val();

        if(currency){
            $("#admin-transfers-shell .transfer-summary .currency").text(currency);
        }
        else{
            $("#admin-transfers-shell .transfer-summary .currency").text("-");
        }

        if(amount){
            $("#admin-transfers-shell .transfer-summary .amount").text(parseFloat(amount).toFixed(2));
        }
        else{
            $("#admin-transfers-shell .transfer-summary .amount").text("-");
        }

        if(recipient){
            $("#admin-transfers-shell .transfer-summary .recipient").text(recipient);
        }
        else{
            $("#admin-transfers-shell .transfer-summary .recipient").text("-");
        }

        if(amount && currency && recipient){
            $.ajax({
                type: "GET",
                url: "/api/admin-dashboard/get-transfer-fee",
                data: { amount: amount, currency: currency },
                success: function (response) {
                    var fee = parseFloat(response.fee);
                    var total = parseFloat(amount) - (parseFloat(amount) * fee);

                    var fee_percentage = fee * 100;

                    fee = fee.toFixed(2);
                    total = total.toFixed(2);
                    
                    $("#admin-transfers-shell .transfer-summary .fee").text(fee_percentage + "%");
                    $("#admin-transfers-shell .transfer-summary .total").text(total + " " + currency);

                },
                error: function (response) {
                    showDialog(response.responseJSON.message, "Error");
                }
            });
        }
        else{
            $("#admin-transfers-shell .transfer-summary .total").text("-");
        }
    }

    // When transfer button is clicked
    $("#admin-transfers-shell .transfer-details .buttons .transfer").on("click", function(e){
        e.preventDefault();

        var currency = $("#admin-transfers-shell .transfer-details #currency").val();
        var amount = $("#admin-transfers-shell .transfer-details #amount").val();
        var recipient = $("#admin-transfers-shell .transfer-details #recipient").val();
        var description = $("#admin-transfers-shell .transfer-details #description").val();

        $.ajax({
            type: "POST",
            url: "/api/admin-dashboard/make-transfer",
            data: { currency: currency, amount: amount, recipient: recipient, description: description },
            success: function (response) {
                showDialog(response.message, "Success", reload=true);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });
    
    /// Admin User Transactions Shell

    // When admin clicks search button
    $("#admin-user-transactions-shell .actions #search-username-button").on("click", function() {
        var username = $("#admin-user-transactions-shell .actions #search-username").val();
        var data = { username: username };

        $.ajax({
            type: "GET",
            url: "/api/admin-dashboard/get-user-transactions-table",
            data: data,
            success: function (response) {
                $("#admin-user-transactions-shell .actions #search-transactions").removeClass("hidden");

                $("#admin-user-transactions-shell #table").html(response.table);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });

    // When the search input is typed in, filter the transactions table
    $("#admin-user-transactions-shell .actions #search-transactions").on("keyup", function(e){
        e.preventDefault();

        var search = $(this).val().toLowerCase();

        $("#admin-user-transactions-shell table.transactions tbody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(search) > -1);
        });
    });
}