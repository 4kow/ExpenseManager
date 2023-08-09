# ExpenseManager
This application helps users with keeping an eye on their spends. It has a bunch of useful functionallities that really help with tracking all money spent and what is left to pay back.

Application is created using Python language and Tkinter library. It provides a good-looking user interface that supports some widgets like the widget to enter the amount or to choose a specific date when adding a new spending.

Libraries used to create this application are:
Tkinter for GUI
SQlite3 for the database
Calendar, datetime and relativedata for handling dates
Messagebox for warning messages
Customtkinter for styling


Functionallities of the application:
There are 3 types of spendings that a user can add to the database:
1. Regular spending: This is added by selecting a month from the combobox with the "Select month" text. Later on, user has to provide the name, category and the amount. This spending is simply added to a database and functions as a single record.
2. Deferred amount spending: This is added by typing the name and selecting a checkbox with the "Deferred amount" text on it. Then, two buttons are being enabled and for this spending, user has to choose the first one with the "Pick date" text. The date picker will pop up, when user can look for a specific date which is a date of the first installment. Later on, if there are more than one date, user checks the combobox on a widget and selects the number of installments from the combobobx. Later, user has to type the category and the total amount that is deferred. This option will add the total amount of records that the user has chosen in the checkbox with the first record on the selected date. The whole amount will be divided by the number of installments.
3. Subscription: This is added by typing the name and selecting a checkbox with the "Deferred amount" text on it. Then, from the two buttons, user has to choose the second one with a "Subscription" text on it. A similar widget will pop up, here user has to choose a date when he activated the subscription. Later, user has to type the category and the amount that is charged monthly. This will add unlimited records on every month with the amount that user entered being charged every month.

The second functionallity of the application is calculating the amounts. There are two types of amounts:
1. Total amount: This is a total amount that the user has spent. 
2. Unpaid amount: This is a total amount that the user will have to spend according to the deferred payments, both installments and subscriptions.
There is a "Mark as paid" button, which is useful to specify if the particular installments has been paid or not. Initially, when the user adds a deferred record, there is no charge that is added to a total amount. Only after marking a speciffic installment as "Paid" when the user will pay the amount in real life, the total spendings amount will get updated, and the amount that is left to spend will decrease.
This solution is very useful for the user to keep controll on the amount that he has to pay and will divide spendings into two parts.

There is also a possibility to sort spendings by category and by month. For exapmple, if user wants to check how much money did he spend on groceries, he can select this category from a dynamically-updating combobox and see the new calculated amount. Also, if the user wants to see how much did he spend in a particular month, he can select any month and check the calculated amount. There is also an option to see how much has been spent on the particular category, in particular month both at once.


