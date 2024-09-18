# Web Bank

This project has two components: physical and virtual.

The virtual component is the bank's website, where users can log into their accounts, view their balance, transfer money, and perform other banking tasks. The website will be hosted on a Linux server. 

The physical component is the POS terminal, built using an ESP32 microcontroller. It will feature an RFID sensor, keypad, and display screen, with the potential addition of a buzzer and/or LED indicator. The microcontroller should have an internet connection to send requests to the server.

<div style="text-align: center;">
    <img src="images/Architecture.png">
</div>