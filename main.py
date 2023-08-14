import tkinter as tk
from tkinter import ttk
import sqlite3
import calendar
from tkcalendar import Calendar
import datetime
import tkinter.messagebox as messagebox
from dateutil.relativedelta import relativedelta
import customtkinter
import os

selected_month_to_add = None
months_to_add = 0
subscription_months_amount_to_add = 0
subscription_month_to_add = 0
selected_sort_month = None
status = "Unpaid"
is_subscription_dict = {}
subscription_date = None


def database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
                                id INTEGER PRIMARY KEY,
                                month TEXT,
                                name TEXT,
                                deferred_amount BOOLEAN,
                                repayment_date TEXT,
                                category TEXT,
                                amount REAL,
                                status TEXT,
                                year INTEGER,
                                is_subscription BOOLEAN
                            )''')
    conn.commit()
    conn.close()


def add_record():
    name = entry_name.get()
    category = entry_category.get()
    amount = entry_amount.get()

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Error", "Invalid amount. Please enter a valid number.")
        return

    if not amount:
        messagebox.showerror("Error", "Amount is required. Please enter a valid amount.")
        return

    if not name:
        messagebox.showerror("Error", "Name is required. Please enter a valid name.")
        return

    if not category:
        messagebox.showerror("Error", "Category is required. Please enter a valid category.")
        return

    if check_deferred_amount.get():
        add_deferred_record(name, category, amount)
    else:
        add_regular_record(name, category, amount)

    update_category_combobox()
    button_subscription.configure(state = tk.DISABLED)
    update_total_amount_label()
    update_unpaid_amount_label()
    show_records()


def add_regular_record(name, category, amount):
    month = month_picker_combobox.get()

    if not month or month == "Select Month":
        messagebox.showerror("Error", "Please select a month.")
        return

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO payments (month, name, deferred_amount, repayment_date, category, amount, status, year, is_subscription) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (month, name, False, "-", category, amount, 'Paid', selected_year, False))

    conn.commit()
    conn.close()

    month_picker_combobox.set("Select Month")
    entry_name.delete(0, tk.END)
    entry_category.delete(0, tk.END)
    entry_amount.delete(0, tk.END)
    button_date_picker.configure(state = tk.DISABLED)

    show_records(year = selected_year)
    update_category_combobox()

    update_total_amount_label()
    update_unpaid_amount_label()


def add_deferred_record(name, category, amount, status = "Unpaid"):
    global repayment_date, selected_month_to_add, months_to_add, subscription_month_to_add, subscription_months_amount_to_add, selected_year

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    unpaid_amount_to_add = amount

    if subscription_date is None:
        # Dodaj pierwszy rekord
        cursor.execute(
            "INSERT INTO payments (month, name, deferred_amount, repayment_date, category, amount, status, year, is_subscription) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (calendar.month_name[repayment_date.month], name, True, repayment_date.strftime("%d-%m-%Y"),
             category, amount / months_to_add, status, selected_year, False))

        # Move the date on one month forward (first record is already added)
        new_repayment_date = repayment_date + relativedelta(months = 1)

        for i in range(months_to_add - 1):  # Subtract 1 because first record is already added

            # Zaktualizuj selected_month_to_add i selected_year dla kolejnego rekordu
            selected_month_to_add = calendar.month_name[new_repayment_date.month]
            new_selected_year = new_repayment_date.year

            cursor.execute(
                "INSERT INTO payments (month, name, deferred_amount, repayment_date, category, amount, status, year, is_subscription) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (calendar.month_name[new_repayment_date.month], name, True, new_repayment_date.strftime("%d-%m-%Y"),
                 category, amount / months_to_add, status, new_selected_year,
                 False))  # Ustawienie statusu dla nowego rekordu

            unpaid_amount_to_add += amount / months_to_add

            new_repayment_date = new_repayment_date + relativedelta(months = 1)

    if subscription_date is not None:

        cursor.execute(
            "INSERT INTO payments (month, name, deferred_amount, repayment_date, category, amount, status, year, is_subscription) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (calendar.month_name[subscription_date.month], name, True, subscription_date.strftime("%d-%m-%Y"),
             category, amount, status, selected_year, True))

        new_subscription_date = subscription_date + relativedelta(months = 1)

        for i in range(subscription_months_amount_to_add - 1):  # Odejmujemy 1, bo pierwszy rekord już został dodany

            selected_month_to_add = calendar.month_name[new_subscription_date.month]
            new_selected_year = new_subscription_date.year
            cursor.execute(
                "INSERT INTO payments (month, name, deferred_amount, repayment_date, category, amount, status, year, is_subscription) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (calendar.month_name[new_subscription_date.month], name, True,
                 new_subscription_date.strftime("%d-%m-%Y"),
                 category, amount, status, new_selected_year, True))  # Ustawienie statusu dla nowego rekordu

            unpaid_amount_to_add += amount

            new_subscription_date = new_subscription_date + relativedelta(months = 1)

    conn.commit()
    conn.close()

    entry_name.delete(0, tk.END)
    entry_category.delete(0, tk.END)
    entry_amount.delete(0, tk.END)
    check_deferred_amount.set(False)
    label_repayment_date.configure(text = "Repayment Date: -")
    button_date_picker.configure(state = tk.DISABLED)

    # Stay in the year-view after adding the record
    show_records(year = selected_year)
    update_category_combobox()

    update_total_amount_label(None, selected_sort_month, selected_year)
    update_unpaid_amount_label(None, selected_sort_month, selected_year)


def create_year_navigation_buttons():
    button_previous_year = customtkinter.CTkButton(entry_frame, text = "<<", command = previous_year)
    button_previous_year.grid(row = 0, column = 0, padx = 5, pady = 5)

    button_next_year = customtkinter.CTkButton(entry_frame, text = ">>", command = next_year)
    button_next_year.grid(row = 0, column = 7, padx = 5, pady = 5)


def previous_year():
    global selected_year, selected_category
    selected_year -= 1
    selected_category = "Select category"
    update_year_label()
    show_records(year = selected_year)
    update_total_amount_label()
    update_unpaid_amount_label()


def next_year():
    global selected_year, selected_category
    selected_year += 1
    selected_category = "Select category"
    update_year_label()
    show_records(year = selected_year)
    update_total_amount_label()
    update_unpaid_amount_label()


def update_year_label():
    global selected_year
    current_year_label.configure(text = f"Year: {selected_year}")


def create_year_picker():
    year_picker_combobox = ttk.Combobox(entry_frame, values = [year for year in range(2023, 2123)], state = "readonly")
    year_picker_combobox.grid(row = 0, column = 1, padx = 5, pady = 5)
    year_picker_combobox.set(selected_year)
    year_picker_combobox.bind("<<ComboboxSelected>>", on_year_selected)
    year_picker_combobox.grid_forget()
    return year_picker_combobox


def create_month_picker():
    months = [""]
    months.extend(calendar.month_name[1:])
    month_picker_combobox = customtkinter.CTkComboBox(master = entry_frame, command = on_month_selected,
                                                      values = months)
    month_picker_combobox.grid(row = 0, column = 1, padx = 5, pady = 5)
    month_picker_combobox.set("Select Month")
    return month_picker_combobox


def on_month_selected(choice):
    global selected_month
    selected_month = None if choice == "Select Month" else choice


def on_year_selected(event):
    global selected_year
    selected_year = event.widget.get()
    show_all_data()
    update_total_amount_label()
    update_unpaid_amount_label()


def delete_selected():
    global subscription_date
    selected_items = tree.selection()
    if not selected_items:
        return

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    for item in selected_items:
        record_id = tree.item(item, 'values')[0]
        cursor.execute("SELECT name, is_subscription FROM payments WHERE id=?", (record_id,))
        record_data = cursor.fetchone()
        name = record_data[0]
        is_subscription = record_data[1]

        if is_subscription:
            # Delete all the records named the same which are subscriptions
            cursor.execute("DELETE FROM payments WHERE name=? AND is_subscription=?", (name, True))
        else:
            cursor.execute("DELETE FROM payments WHERE id=?", (record_id,))

    conn.commit()
    conn.close()

    show_records()
    update_category_combobox()
    update_total_amount_label()
    update_unpaid_amount_label()


def create_amount_button(tree, record_id, amount):
    def on_button_click(record_id):
        open_amount_widget(record_id)

    amount_button = customtkinter.CTkButton(tree, text = amount, command = lambda id = record_id: on_button_click(id))
    return amount_button


def open_amount_widget():
    amount_widget = customtkinter.CTkToplevel(root)
    amount_widget.title = "Enter amount"
    amount_widget.geometry("215x330")
    amount_widget.focus()

    def on_digit_click(digit):
        current_value = entry_amount.get()
        entry_amount.delete(0, tk.END)
        entry_amount.insert(tk.END, current_value + digit)

    def on_coma_click():
        current_value = entry_amount.get()
        if '.' not in current_value:
            entry_amount.delete(0, tk.END)
            entry_amount.insert(tk.END, current_value + '.')

    def on_backspace_click():
        current_value = entry_amount.get()
        entry_amount.delete(0, tk.END)
        entry_amount.insert(tk.END, current_value[:-1])

    def on_ok_click():
        amount_widget.destroy()

    digits = [
        '7', '8', '9',
        '4', '5', '6',
        '1', '2', '3',
        '0', '.', '⌫'
    ]

    button_font = ("Helvetica", 13)

    row, col = 1, 0
    for digit in digits:
        if digit == '⌫':
            btn = customtkinter.CTkButton(amount_widget, text = digit, font = button_font, width = 50, height = 50,
                                          command = on_backspace_click)
        elif digit == '.':
            btn = customtkinter.CTkButton(amount_widget, text = digit, font = button_font, width = 50, height = 50,
                                          command = on_coma_click)
        else:
            btn = customtkinter.CTkButton(amount_widget, text = digit, font = button_font,
                                          width = 50, height = 50, command = lambda d = digit: on_digit_click(d))

        btn.grid(row = row, column = col, padx = 10, pady = 10)
        col += 1
        if col == 3:
            col = 0
            row += 1

    ok_button = customtkinter.CTkButton(amount_widget, text = "OK", command = on_ok_click)
    ok_button.grid(row = row, column = 0, columnspan = 3, padx = 10, pady = 5)


def open_date_picker():
    def on_date_select():
        global repayment_date, selected_month_to_add, months_to_add

        selected_date_str = calendar_widget.get_date()
        repayment_date = datetime.datetime.strptime(selected_date_str, "%m/%d/%y").date()
        selected_month_to_add = calendar.month_name[repayment_date.month]

        if checked.get():
            months_to_add = int(combobox_months.get())
        else:
            months_to_add = 1

        label_repayment_date.configure(text = f"Repayment Date: {selected_date_str}")
        calendar_toplevel.destroy()

    def checkbox_checked():
        if checked.get():
            combobox_months.configure(state = "normal")
        else:
            combobox_months.configure(state = "disabled")

    calendar_toplevel = customtkinter.CTkToplevel(root)
    calendar_toplevel.title("Select date")
    calendar_toplevel.geometry("400x400")
    calendar_toplevel.focus()

    today = datetime.date.today()
    calendar_widget = Calendar(calendar_toplevel, selectmode = 'day', year = today.year, month = today.month,
                               day = today.day)
    calendar_widget.pack(pady = 20)

    checked = tk.BooleanVar()
    checkbox_add_months = customtkinter.CTkCheckBox(calendar_toplevel, text = "no. of installments", variable = checked,
                                                    command = checkbox_checked)
    checkbox_add_months.pack(pady = 10)

    months = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
              "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"]
    combobox_months = customtkinter.CTkComboBox(calendar_toplevel, values = months, state = "disabled")
    combobox_months.pack(pady = 10)

    ok_button = customtkinter.CTkButton(calendar_toplevel, text = "OK", command = on_date_select)
    ok_button.pack(pady = 10)


def open_subscription_picker():
    def on_subscription_date_select():
        global subscription_date, subscription_month_to_add, subscription_months_amount_to_add
        selected_date_subscription = calendar_subscription_widget.get_date()
        subscription_date = datetime.datetime.strptime(selected_date_subscription, "%m/%d/%y").date()
        subscription_month_to_add = calendar.month_name[subscription_date.month]
        subscription_months_amount_to_add = 1200

        label_repayment_date.configure(text = f"Repayment Date: {selected_date_subscription}")
        calendar_toplevel_s.destroy()

    calendar_toplevel_s = customtkinter.CTkToplevel(root)
    calendar_toplevel_s.title("Select date")
    calendar_toplevel_s.geometry("400x400")
    calendar_toplevel_s.focus()

    today = datetime.date.today()
    calendar_subscription_widget = Calendar(calendar_toplevel_s, selectmode = 'day', year = today.year,
                                            month = today.month,
                                            day = today.day)
    calendar_subscription_widget.pack(pady = 20)

    ok_button = customtkinter.CTkButton(calendar_toplevel_s, text = "OK", command = on_subscription_date_select)
    ok_button.pack(pady = 10)


def show_records(month = None, category = None, year = None):
    global status

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    months_mapping = {month: index for index, month in enumerate(calendar.month_name[1:])}

    if not year:
        year = selected_year

    if month_sort_combobox.get() != "Select month for sort" and category_picker_combobox.get() != "Select category":
        month = month_sort_combobox.get()
        category = category_picker_combobox.get()

        cursor.execute("SELECT * FROM payments WHERE month=? AND category=? AND year=?", (month, category, year))
    elif month is None and category is None:
        cursor.execute("SELECT * FROM payments WHERE year=?", (year,))
    elif month is None:
        cursor.execute("SELECT * FROM payments WHERE category=? AND year=?", (category, year))
    elif category is None:
        cursor.execute("SELECT * FROM payments WHERE month=? AND year=?", (month, year))
    else:
        cursor.execute("SELECT * FROM payments WHERE month=? AND category=? AND year=?", (month, category, year))

    records = sorted(cursor.fetchall(), key = lambda x: (months_mapping[x[1]], x[4], x[5]))

    tree.delete(*tree.get_children())

    for record in records:
        deferred_amount = "Yes" if record[3] else "No"
        amount = f"{record[6]:.2f} PLN" if record[6] is not None else ""
        status = record[7] if record[3] else ""  # Ustawiamy status tylko dla deferred_record
        tree.insert("", "end",
                    values = (record[0], record[1], record[2], deferred_amount, record[4], record[5], amount, status))
        is_subscription_dict[record[0]] = record[9]

    conn.close()

    if month_sort_combobox.get() != "Select month for sort" and category_picker_combobox.get() != "Select category":
        update_total_amount_label(calculate_total_amount(month = month, category = category, year = year), month, year)
        update_unpaid_amount_label(calculate_unpaid_amount(month = month, category = category, year = year), month,
                                   year)
    elif month and category:
        update_total_amount_label(calculate_total_amount(month = month, category = category, year = year), month, year)
        update_unpaid_amount_label(calculate_unpaid_amount(month = month, category = category, year = year), month,
                                   year)
    elif month:
        update_total_amount_label(calculate_total_amount(month = month, year = year), month, year)
        update_unpaid_amount_label(calculate_unpaid_amount(month = month, year = year), month, year)
    elif category:
        update_total_amount_label(calculate_total_amount(category = category, year = year), None, year)
        update_unpaid_amount_label(calculate_unpaid_amount(category = category, year = year), None, year)
    else:
        update_total_amount_label(calculate_total_amount(year = year), None, year)
        update_unpaid_amount_label(calculate_unpaid_amount(year = year), None, year)

    conn.close()


def calculate_total_amount(month = None, category = None, year = None):
    if year is None:
        year = selected_year

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = "SELECT SUM(amount) FROM payments WHERE status='Paid' AND year=?"
    parameters = [year]

    if month is not None:
        query += " AND month=?"
        parameters.append(month)

    if category is not None:
        query += " AND category=?"
        parameters.append(category)

    cursor.execute(query, tuple(parameters))

    total_amount = cursor.fetchone()[0] or 0

    conn.close()
    return total_amount


def calculate_unpaid_amount(month = None, category = None, year = None):
    if year is None:
        year = selected_year

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = "SELECT SUM(amount) FROM payments WHERE status='Unpaid' AND year=?"
    parameters = [year]

    if month is not None:
        query += " AND month=?"
        parameters.append(month)

    if category is not None:
        query += " AND category=?"
        parameters.append(category)

    cursor.execute(query, tuple(parameters))

    unpaid_amount = cursor.fetchone()[0] or 0

    conn.close()
    return unpaid_amount


def update_total_amount_label(total_amount_to_add = None, month = None, year = None):
    global selected_sort_month, selected_category

    if year is None:
        year = selected_year

    selected_sort_month = selected_sort_month if selected_sort_month != "Select month for sort" else None

    if selected_category == "Select category":
        if selected_sort_month is None:
            total_amount = calculate_total_amount(year = year)
        else:
            total_amount = calculate_total_amount(month = selected_sort_month, year = year)
    else:
        if selected_sort_month is None:
            total_amount = calculate_total_amount(category = selected_category, year = year)
        else:
            total_amount = calculate_total_amount(month = selected_sort_month, category = selected_category,
                                                  year = year)

    if total_amount_to_add is not None and month:
        total_amount += total_amount_to_add

    total_amount_label.configure(text = f"Total Amount: {total_amount:.2f} PLN")


def update_unpaid_amount_label(unpaid_amount_to_add = None, month = None, year = None):
    global selected_sort_month, selected_category

    if year is None:
        year = selected_year

    selected_sort_month = selected_sort_month if selected_sort_month != "Select month for sort" else None

    if month and not selected_sort_month:
        selected_sort_month = month

    if selected_category == "Select category":
        if selected_sort_month is None:
            unpaid_amount = calculate_unpaid_amount(year = year)
        else:
            unpaid_amount = calculate_unpaid_amount(month = selected_sort_month, year = year)
    else:
        if selected_sort_month is None:
            unpaid_amount = calculate_unpaid_amount(category = selected_category, year = year)
        else:
            unpaid_amount = calculate_unpaid_amount(month = selected_sort_month, category = selected_category,
                                                    year = year)

    if unpaid_amount_to_add is not None and month:
        unpaid_amount += unpaid_amount_to_add

    unpaid_amount_label.configure(text = f"Unpaid Amount: {unpaid_amount:.2f} PLN")


def update_category_combobox():
    categories = get_categories()
    category_picker_combobox.configure(values = categories)
    category_picker_combobox.set("Select category")


def show_all_data():
    global selected_month, selected_category, selected_year, selected_sort_month

    selected_month = None
    selected_category = "Select category"
    category_picker_combobox.set("Select category")

    month_picker_combobox.set("Select Month")
    year_picker_combobox.set(selected_year)
    month_sort_combobox.set("Select month for sort")

    root.title(f"Expenses Manager - {selected_year}")

    selected_sort_month = None
    show_records(year = selected_year)

    update_total_amount_label()
    update_unpaid_amount_label()
    update_category_combobox()


def on_record_select():
    selected_items = tree.selection()
    if not selected_items:
        return

    item = tree.item(selected_items[0])
    record_data = item['values']

    entry_name.delete(0, tk.END)
    entry_name.insert(0, record_data[2])

    check_deferred_amount.set(record_data[3])

    entry_category.delete(0, tk.END)
    entry_category.insert(0, record_data[5])


def on_category_selected(choice):
    global selected_category

    selected_category = choice

    if selected_category == "Select category":
        # Clear comboboxes
        month_picker_combobox.set("Select Month")
        category_picker_combobox.set("Select category")
        show_records(year = selected_year)
    else:
        show_records(category = selected_category, year = selected_year)

    update_total_amount_label(None, selected_sort_month, selected_year)
    update_unpaid_amount_label(None, selected_sort_month, selected_year)


def get_categories():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    list_of_categories = cursor.execute("SELECT DISTINCT category FROM payments").fetchall()
    categories = [category[0] for category in list_of_categories]

    conn.close()

    return categories


def create_category_combobox():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    list_of_categories = cursor.execute("SELECT DISTINCT category FROM payments").fetchall()
    categories = ["Select category"] + [category[0] for category in list_of_categories]

    categories_picker_combobox = customtkinter.CTkComboBox(master = entry_frame, values = categories,
                                                           command = on_category_selected, width = 200)
    categories_picker_combobox.grid(row = 0, column = 4, padx = 5, pady = 5)
    categories_picker_combobox.set("Select category")

    conn.close()

    return categories_picker_combobox


def create_month_sort_combobox():
    months = ["Select month for sort"]
    months.extend(calendar.month_name[1:])
    month_sort_combobox = customtkinter.CTkComboBox(master = entry_frame, command = on_month_sort_selected,
                                                    values = months, width = 200)
    month_sort_combobox.grid(row = 1, column = 4, padx = 5, pady = 5)
    month_sort_combobox.set("Select month for sort")
    return month_sort_combobox


def on_month_sort_selected(choice):
    global selected_sort_month

    selected_sort_month = choice

    if selected_sort_month == "Select month for sort":
        month_picker_combobox.set("Select Month")
        month_sort_combobox.set("Select month for sort")
        show_records(year = selected_year)
    else:
        show_records(month = selected_sort_month, year = selected_year)

    update_total_amount_label(None, selected_sort_month, selected_year)
    update_unpaid_amount_label(None, selected_sort_month, selected_year)


def mark_as_paid(unpaid_amount_to_add = 0.0, total_amount_to_add = 0.0):
    global status, selected_sort_month, selected_category

    selected_items = tree.selection()
    if not selected_items:
        return

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    unpaid_amount_to_subtract = 0.0

    for item in selected_items:
        record_id = tree.item(item, 'values')[0]
        record_status = tree.item(item, 'values')[7]

        if record_status == "Unpaid":
            record_amount = float(tree.item(item, 'values')[6].split()[0])
            unpaid_amount_to_subtract += record_amount

        unpaid_amount_to_add = unpaid_amount_to_add - unpaid_amount_to_subtract
        total_amount_to_add = total_amount_to_add + unpaid_amount_to_subtract
        cursor.execute("UPDATE payments SET status=? WHERE id=?", ("Paid", record_id))

        # Update status in treeview
        tree.item(item, values = (
        record_id, tree.item(item, 'values')[1], tree.item(item, 'values')[2], tree.item(item, 'values')[3],
        tree.item(item, 'values')[4], tree.item(item, 'values')[5], tree.item(item, 'values')[6], "Paid"))

    conn.commit()
    conn.close()

    status = "Paid"

    update_total_amount_label()
    update_unpaid_amount_label()


def change_theme():
    button_mode = switch.get()
    theme_value = button_mode
    if button_mode is 1:
        customtkinter.set_appearance_mode("dark")
        treestyle = ttk.Style()
        treestyle.theme_use('clam')
        treestyle.configure("Treeview", background = "#212121", foreground = "light gray", fieldbackground = "212121",
                            borderwidth = 3, bordercolor = "gray")
        treestyle.configure("Treeview.Heading", font = ("Araboto normal", 10), background = "#1F538D",
                            foreground = "light gray")
        treestyle.map('Treeview', background = [('selected', 'white')], foreground = [('selected', 'black')])
    else:
        customtkinter.set_appearance_mode("light")
        treestyle = ttk.Style()
        treestyle.theme_use('clam')
        treestyle.configure("Treeview", background = "#e5e5e5", foreground = "black", fieldbackground = "#e5e5e5",
                            borderwidth = 3, bordercolor = "gray")
        treestyle.configure("Treeview.Heading", font = ("Araboto normal", 10), background = "#3a7ebf",
                            foreground = "white")
        treestyle.map('Treeview', background = [('selected', 'white')], foreground = [('selected', 'black')])

    save_theme(theme_value)

    lines_with_treeview_settings = read_settings_from_file("theme.txt")
    apply_treeview_style_from_file(lines_with_treeview_settings)
    switch_var.set(theme_value)


def save_theme(theme_value):
    file_path = os.path.expanduser("~")
    file_path = os.path.join(file_path, "theme.txt")
    with open(file_path, "w") as file:
        file.write(f"{theme_value}\n")
        if theme_value == 1:
            write_treeview_settings(file, "#212121", "light gray", "212121", "gray", "#1F538D", "light gray", "white",
                                    "black")
        else:
            write_treeview_settings(file, "#e5e5e5", "black", "#e5e5e5", "gray", "#3a7ebf", "white", "white", "black")


def write_treeview_settings(file, bg1, fg1, fb1, bc1, bg2, fg2, fb2, bc2):
    file.write(f"background1:{bg1}\n")
    file.write(f"foreground1:{fg1}\n")
    file.write(f"fieldbackground1:{fb1}\n")
    file.write(f"bordercolor1:{bc1}\n")
    file.write(f"background2:{bg2}\n")
    file.write(f"foreground2:{fg2}\n")
    file.write(f"fieldbackground2:{fb2}\n")
    file.write(f"bordercolor2:{bc2}\n")


def load_theme():
    try:
        file_path = os.path.expanduser("~")
        file_path = os.path.join(file_path, "theme.txt")

        with open(file_path, "r") as file:
            lines = file.readlines()
            theme_value = int(lines[0].strip())
            return theme_value
    except FileNotFoundError:
        return 0


def apply_treeview_style_from_file(style_lines):
    treestyle = ttk.Style()
    treestyle.theme_use('clam')

    tree_style_settings = {}
    for line in style_lines:
        if ":" in line:
            key, value = line.strip().split(":")
            tree_style_settings[key] = value

    if "background1" in tree_style_settings:
        treestyle.configure("Custom.Treeview", background = tree_style_settings["background1"])
    if "foreground1" in tree_style_settings:
        treestyle.configure("Custom.Treeview", foreground = tree_style_settings["foreground1"])
    if "fieldbackground1" in tree_style_settings:
        treestyle.configure("Custom.Treeview", fieldbackground = tree_style_settings["fieldbackground1"])
    if "bordercolor1" in tree_style_settings:
        treestyle.configure("Custom.Treeview", bordercolor = tree_style_settings["bordercolor1"])
    if "background2" in tree_style_settings:
        treestyle.configure("Custom.Treeview.Heading", background = tree_style_settings["background2"])
    if "foreground2" in tree_style_settings:
        treestyle.configure("Custom.Treeview.Heading", foreground = tree_style_settings["foreground2"])
    if "fieldbackground2" in tree_style_settings:
        treestyle.configure("Custom.Treeview.Heading", fieldbackground = tree_style_settings["fieldbackground2"])
    if "bordercolor2" in tree_style_settings:
        treestyle.configure("Custom.Treeview.Heading", bordercolor = tree_style_settings["bordercolor2"])

    treestyle.map('Custom.Treeview', background = [('selected', 'white')], foreground = [('selected', 'black')])


database()
current_year = datetime.datetime.now().year
selected_year = current_year

root = customtkinter.CTk()


def on_deferred_amount_checked():
    if check_deferred_amount.get():
        button_date_picker.configure(state = tk.NORMAL)
        button_subscription.configure(state = tk.NORMAL)
    else:
        button_date_picker.configure(state = tk.DISABLED)
        button_subscription.configure(state = tk.DISABLED)


window_width = 1100
window_height = 890
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

root.title("Expenses Manager")

current_year_label = customtkinter.CTkLabel(root, text = f"Year: {selected_year}", font = ("Helvetica", 16, "bold"))
current_year_label.pack(padx = 10, pady = 5)

# Container for the upper part of the app
entry_frame = customtkinter.CTkFrame(master = root)
entry_frame.pack(side = tk.TOP, padx = 10, pady = 10)

label_sort = customtkinter.CTkLabel(entry_frame, text = "Sort by category:")
label_sort.grid(row = 0, column = 3, padx = 5, pady = 5)

label_sort = customtkinter.CTkLabel(entry_frame, text = "Sort by month:")
label_sort.grid(row = 1, column = 3, padx = 5, pady = 5)

label_name = customtkinter.CTkLabel(entry_frame, text = "Name:")
label_name.grid(row = 1, column = 0, padx = 5, pady = 5)
entry_name = customtkinter.CTkEntry(entry_frame)
entry_name.grid(row = 1, column = 1, padx = 5, pady = 5)

check_deferred_amount = tk.BooleanVar()
checkbutton_deferred_amount = customtkinter.CTkCheckBox(entry_frame, text = "Deferred amount",
                                                        variable = check_deferred_amount,
                                                        command = on_deferred_amount_checked)
checkbutton_deferred_amount.grid(row = 2, columnspan = 2, padx = 5, pady = 5)

label_repayment_date = customtkinter.CTkLabel(entry_frame, text = "Repayment date:")
label_repayment_date.grid(row = 3, column = 0, padx = 5, pady = 5)
button_date_picker = customtkinter.CTkButton(entry_frame, text = "Pick date", command = open_date_picker,
                                             state = tk.DISABLED)
button_date_picker.grid(row = 3, column = 2, padx = 5, pady = 5)
button_subscription = customtkinter.CTkButton(entry_frame, text = "Subscription", command = open_subscription_picker,
                                              state = tk.DISABLED)
button_subscription.grid(row = 3, column = 3, padx = 5, pady = 5)

label_category = customtkinter.CTkLabel(entry_frame, text = "Category:")
label_category.grid(row = 4, column = 0, padx = 5, pady = 5)
entry_category = customtkinter.CTkEntry(entry_frame)
entry_category.grid(row = 4, column = 1, padx = 5, pady = 5)

label_amount = customtkinter.CTkLabel(entry_frame, text = "Amount:")  # Etykieta dla pola "amount"
label_amount.grid(row = 5, column = 0, padx = 5, pady = 5)
entry_amount = customtkinter.CTkEntry(entry_frame)  # Pole do wprowadzania "amount"
entry_amount.grid(row = 5, column = 1, padx = 5, pady = 5)
button_open_amount_widget = customtkinter.CTkButton(entry_frame, text = "Amount", command = open_amount_widget)
button_open_amount_widget.grid(row = 5, column = 2, padx = 5, pady = 5)

# Add record button
button_add = customtkinter.CTkButton(entry_frame, text = "Add spending", command = add_record)
button_add.grid(row = 6, column = 1, columnspan = 2, padx = 5, pady = 10, sticky = "w")

# Treeview container
treeview_frame = customtkinter.CTkFrame(master = root)
treeview_frame.pack(side = tk.TOP, padx = 10, pady = 10)

# Treeview
root.bind("<<TreeviewSelect>>", lambda event: root.focus_set())

tree = ttk.Treeview(treeview_frame, columns = (
"ID", "Month", "Name", "Deferred Amount", "Repayment Date", "Category", "Amount", "Status"), style = "Custom.Treeview")
tree.pack(expand = True)
tree["height"] = 17

# Setting up the treeview
tree.heading("#1", text = "ID")
tree.heading("#2", text = "Month")
tree.heading("#3", text = "Name")
tree.heading("#4", text = "Deferred Amount")
tree.heading("#5", text = "Repayment Date")
tree.heading("#6", text = "Category")
tree.heading("#7", text = "Amount")
tree.heading("#8", text = "Status")

tree.column("#1", stretch = False, width = 50)
tree.column("#2", stretch = True, width = 100)
tree.column("#3", stretch = True, width = 150)
tree.column("#4", stretch = True, width = 150)
tree.column("#5", stretch = True, width = 150)
tree.column("#6", stretch = True, width = 100)
tree.column("#7", stretch = True, width = 100)
tree.column("#8", stretch = True, width = 60)

# Assigning the delete_selected() function to a "delete" event
tree.bind("<Delete>", delete_selected)

# Container for the bottom part of the app
calendar_frame = customtkinter.CTkFrame(root)
calendar_frame.pack(side = tk.TOP, padx = 10, pady = 10)

months = [month for month in calendar.month_name[1:]]
month_buttons = []

# Buttons on the bottom part of the app
button_show_all = customtkinter.CTkButton(calendar_frame, text = "Show All", command = show_all_data)
button_show_all.grid(row = 3, column = 0, columnspan = 2, padx = 5, pady = 5)
button_delete_selected = customtkinter.CTkButton(calendar_frame, text = "Delete Selected", command = delete_selected)
button_delete_selected.grid(row = 3, column = 2, padx = 5, pady = 5)

button_mark_as_paid = customtkinter.CTkButton(calendar_frame, text = "Mark as Paid", command = mark_as_paid)
button_mark_as_paid.grid(row = 3, column = 3, padx = 5, pady = 5)

total_amount_label = customtkinter.CTkLabel(calendar_frame, text = "Total Amount: 0.00 PLN")
total_amount_label.grid(row = 4, column = 0, columnspan = len(months[4:8]), padx = 5, pady = 5)

unpaid_amount_label = customtkinter.CTkLabel(calendar_frame, text = "Unpaid Amount: 0.00 PLN")
unpaid_amount_label.grid(row = 5, column = 0, columnspan = len(months[4:8]), padx = 5, pady = 5)

current_theme = str(load_theme())
switch_var = customtkinter.StringVar()

switch = customtkinter.CTkSwitch(calendar_frame, text = "Switch mode", command = change_theme,
                                 variable = switch_var, onvalue = 1, offvalue = 0)
switch.grid(row = 6, column = 2, padx = 5, pady = 5)

if int(current_theme) is 0:
    switch.deselect()
else:
    switch.select()


customtkinter.set_appearance_mode("dark" if current_theme == "1" else "light")
customtkinter.set_default_color_theme("dark-blue")


def read_settings_from_file(file_path):
    file_path = os.path.join(os.path.expanduser("~"), "theme.txt")
    with open(file_path, "r") as file:
        lines = file.readlines()
    return lines


lines_with_treeview_settings = read_settings_from_file("theme.txt")
apply_treeview_style_from_file(lines_with_treeview_settings)

create_year_navigation_buttons()
month_sort_combobox = create_month_sort_combobox()
year_picker_combobox = create_year_picker()
month_picker_combobox = create_month_picker()
category_picker_combobox = create_category_combobox()
selected_month = None
show_all_data()

root.mainloop()
