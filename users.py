import csv
import os

def get_or_add_user(user_id, city=None):
    filename = "users.csv"
    users = {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            users = {rows[0]: rows[1] for rows in reader}
    if str(user_id) not in users and city:
        users[str(user_id)] = city
        with open(filename, "w", encoding="utf-8") as file:
            writer = csv.writer(file)
            for key, value in users.items():
                writer.writerow([key, value])
    return users.get(str(user_id), "Неизвестно")
