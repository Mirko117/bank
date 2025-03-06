

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

    // When the search input is typed in, filter the transactions table
    $("#transactions-shell .search-wrapper .search").on("keyup", function(e){
        e.preventDefault();

        var search = $(this).val().toLowerCase();

        $("#transactions-shell table.transactions tbody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(search) > -1);
        });
    });

    // When export button is clicked
    $("#transactions-shell .actions .export").on("click", function(e){
        e.preventDefault();

        $.ajax({
            type: "GET",
            url: "/api/dashboard/export-transactions-dialog",
            success: function (response) {
                var html = response.html;
                var title = response.title;
                showDialog(html, title);
                loadExportTransactionsDialogListeners()
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });

    });

    // When add currency button is clicked
    $("#currencies-shell .all-currencies .add-currency").on("click", function(e) {
        e.preventDefault();

        $.ajax({
            type: "GET",
            url: "/api/dashboard/add-currency-dialog",
            success: function (response) {
                var html = response.html;
                var title = response.title;

                $("<div>" + html + "</div>").dialog({
                    title: title,
                    modal: true,
                    resizable: false,
                    draggable: false,
                    position: { my: "top+100", at: "top", of: window },
                    buttons: {
                        Ok: function(){
                            currency = $("#add-currency-dialog #select-currency").val();

                            $.ajax({
                                type: "POST",
                                url: "/api/dashboard/add-currency",
                                data: { currency: currency },
                                success: function (response) {
                                    showDialog(response.message, "Success", reload=true);
                                },
                                error: function (response) {
                                    showDialog(response.responseJSON.message, "Error");
                                }
                            });
                            $(this).dialog('close');
                            return true;
                        }
                    },
                    close: function(){
                        $(this).dialog('destroy');
                    }
                });
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });

    // Currency exchange input listener
    $("#currencies-shell .currency-exchange input").on("input", function(e){
        handleCurrencyExchange();
    });

    // Currency exchange select listener
    $("#currencies-shell .currency-exchange select").on("input", function(e){
        handleCurrencyExchange();
    });
    
    // Handle currency exchange 
    function handleCurrencyExchange(){
        var amount = $("#currencies-shell .currency-exchange #amount").val();
        var from = $("#currencies-shell .currency-exchange #from").val();
        var to = $("#currencies-shell .currency-exchange #to").val();

        if(parseFloat(amount) <= 0 || from == to || !amount || !from || !to){
            $("#currencies-shell .exchange-result").addClass("hidden");
            return;
        }

        if(amount && from && to){
            $.ajax({
                type: "GET",
                url: "/api/dashboard/exchange-currencies",
                data: { amount: amount, from: from, to: to },
                success: function (response) {
                    $("#currencies-shell .exchange-result").removeClass("hidden");
                    $("#currencies-shell .currency-exchange #exchange-rate").text(response.exchange_rate);
                    $("#currencies-shell .currency-exchange #result").text(response.result);
                },
                error: function (response) {
                    showDialog(response.responseJSON.message, "Error");
                }
            });
        }
    }

    // When exchange currency button is clicked
    $("#currencies-shell .exchange-result #exchange-currency").on("click", function(e){
        e.preventDefault();

        var amount = $("#currencies-shell .currency-exchange #amount").val();
        var from = $("#currencies-shell .currency-exchange #from").val();
        var to = $("#currencies-shell .currency-exchange #to").val();

        if(parseFloat(amount) <= 0 || from == to){
            return;
        }

        $.ajax({
            type: "POST",
            url: "/api/dashboard/exchange-currencies",
            data: { amount: amount, from: from, to: to },
            success: function (response) {
                showDialog(response.message, "Success", reload=true);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });

    // When cancel exchange button is clicked
    $("#currencies-shell .exchange-result #cancel-exchange").on("click", function(e){
        e.preventDefault();
        $("#currencies-shell .exchange-result").addClass("hidden");
        $("#currencies-shell .currency-exchange #amount").val("");
        $("#currencies-shell .currency-exchange #to").val("");
    });


    function loadExportTransactionsDialogListeners(){
        $("#export-transactions-dialog .export-option").on("click", function(e){
            e.preventDefault();
    
            var url = $(this).attr("href");
    
            $.ajax({
                type: "HEAD",
                url: url,
                success: function (response) {
                    window.location.href = url;
                },
                error: function (response) {
                    showDialog(response.responseJSON.message, "Error");
                }
            });
        });
    }

    // Currency input listener
    $("#transfers-shell .transfer-details #currency").on("change", function(e){
        e.preventDefault();
        handleTransferSumarry();
    });

    // Amount input listener
    $("#transfers-shell .transfer-details #amount").on("change", function(e){
        e.preventDefault();
        handleTransferSumarry();
    });

    // Recipient input listener
    $("#transfers-shell .transfer-details #recipient").on("change", function(e){
        e.preventDefault();
        handleTransferSumarry();
    });

    // Handle transfer summary when user inputs data
    function handleTransferSumarry(){
        var currency = $("#transfers-shell .transfer-details #currency").val();
        var amount = $("#transfers-shell .transfer-details #amount").val();
        var recipient = $("#transfers-shell .transfer-details #recipient").val();

        if(currency){
            $("#transfers-shell .transfer-summary .currency").text(currency);
        }
        else{
            $("#transfers-shell .transfer-summary .currency").text("-");
        }

        if(amount){
            $("#transfers-shell .transfer-summary .amount").text(parseFloat(amount).toFixed(2));
        }
        else{
            $("#transfers-shell .transfer-summary .amount").text("-");
        }

        if(recipient){
            $("#transfers-shell .transfer-summary .recipient").text(recipient);
        }
        else{
            $("#transfers-shell .transfer-summary .recipient").text("-");
        }

        if(amount && currency && recipient){
            $.ajax({
                type: "GET",
                url: "/api/dashboard/get-transfer-fee",
                data: { amount: amount, currency: currency },
                success: function (response) {
                    var fee = parseFloat(response.fee);
                    var total = parseFloat(amount) + (parseFloat(amount) * fee);

                    var fee_percentage = fee * 100;

                    fee = fee.toFixed(2);
                    total = total.toFixed(2);
                    
                    $("#transfers-shell .transfer-summary .fee").text(fee_percentage + "%");
                    $("#transfers-shell .transfer-summary .total").text(total + " " + currency);

                },
                error: function (response) {
                    showDialog(response.responseJSON.message, "Error");
                }
            });
        }
        else{
            $("#transfers-shell .transfer-summary .total").text("-");
        }
    }

    // When transfer button is clicked
    $("#transfers-shell .transfer-details .buttons .transfer").on("click", function(e){
        e.preventDefault();

        var currency = $("#transfers-shell .transfer-details #currency").val();
        var amount = $("#transfers-shell .transfer-details #amount").val();
        var recipient = $("#transfers-shell .transfer-details #recipient").val();
        var description = $("#transfers-shell .transfer-details #description").val();

        $.ajax({
            type: "POST",
            url: "/api/dashboard/make-transfer",
            data: { currency: currency, amount: amount, recipient: recipient, description: description },
            success: function (response) {
                showDialog(response.message, "Success", reload=true);
            },
            error: function (response) {
                showDialog(response.responseJSON.message, "Error");
            }
        });
    });
}

