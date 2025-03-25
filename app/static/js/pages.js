
$(document).ready(function() {
    // Navbar
    showLanguagesWhenClick();
    showLanguagesWhenClickSidebar();
    changeLanguageWhenClick();

    // Currency exchange
    addExchangeEventListeners();
});


function showLanguagesWhenClick(){
    // Show languages when clicking on languages the button
    $("#show-languages").on("click", function(e){
        e.preventDefault();
        $("#main-nav .group").each(function(){
            $(this).toggleClass('hidden');
        });
    });

    // Hide languages when clicking on the back arrow
    $("#show-languages-back").on("click", function(e){
        e.preventDefault();
        $("#main-nav .group").each(function(){
            $(this).toggleClass('hidden');
        });
    });
}

function showLanguagesWhenClickSidebar(){
    // Show languages when clicking on languages the button
    $("#show-languages-sidebar").on("click", function(e){
        e.preventDefault();
        $("#sidebar li").each(function(){
            $(this).toggleClass('hidden');
        });
    });

    // Go back when clicking on the back arrow
    $("#show-languages-sidebar-back").on("click", function(e){
        e.preventDefault();
        $("#sidebar li").each(function(){
            $(this).toggleClass('hidden');
        });
    });
}

function changeLanguageWhenClick(){
    $('.language-option').on("click", function() {
        console.log($(this).val());
        var selectedLanguage = $(this).attr('value');
        $.ajax({
            url: '/set_language/' + selectedLanguage,
            type: 'POST',
            success: function(response) {
                if (response.status.includes("Language changed")) {
                    location.reload();
                } else {
                    alert(response.status);
                }
            },
            error: function() {
                alert('Error changing language');
            }
        });
    });
}

function toggleHidden(element){
    $(element).toggleClass('hidden');
}


/// Currency exchange

function addExchangeEventListeners(){
    $('section#converter #currency-exchange a#exchange-button').on('click', function(e){
        e.preventDefault();

        var amount = $('section#converter #currency-exchange .exchange-fields input.amount').val();
        var fromCurrency = $('section#converter #currency-exchange .exchange-fields select.from').val();
        var toCurrency = $('section#converter #currency-exchange .exchange-fields select.to').val();

        if (!amount || !fromCurrency || !toCurrency){
            showDialog("Please fill all the fields", "Error");
            return;
        }

        if (fromCurrency == toCurrency){
            showDialog("You can't exchange the same currency", "Error");
            return;
        }

        if (amount <= 0){
            showDialog("Amount must be greater than 0", "Error");
            return;
        }

        $.ajax({
            url: '/exchange-currencies',
            type: 'GET',
            data: {
                amount: amount,
                from: fromCurrency,
                to: toCurrency
            },
            success: function(response) {
                if (response.status == "success") {
                    console.log(response);
                    $('section#converter #currency-exchange .exchange-result').removeClass('hidden');
                    $('section#converter #currency-exchange .exchange-result .exchange-rate .exchange-rate').text(response.exchange_rate);
                    $('section#converter #currency-exchange .exchange-result .result .result').text(response.result);
                } else {
                    showDialog(response.message, "Error");
                }
            },
            error: function() {
                showDialog('Error exchanging currency', 'Error');
            }
        });
    });
}


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