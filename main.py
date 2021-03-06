import sys

import pyperclip
import stdiomask

import encryptors
from database import Database

# -----------------CONSTANTS THAT USER CAN CHANGE-----------------------------------------------
# Filename of the data base that will be created
PASSWORD_DATABASE = "password.db"
# Name to show in the database to store the public key
MASTER_KEY_NAME_IN_DB = "public_key"
# String to add to our key to salt it before hashing and convert it in a public key,
# could be anything you want, you don't have to remember it
SALT = "AnYtHiNg"
# ----------------------------------------------------------------------------------------------

passwords_db = Database(PASSWORD_DATABASE)


def menu():
    print()
    print("-" * 60)
    print("\nWhat do you want to do?", end="\n\n")
    print("\t1) Get a password")
    print("\t2) Create a new password")
    print("\t3) Save a password")
    print("\t4) Change a password")
    print("\t5) Delete a password")
    print("\t6) See a list of all the sites, users and passwords")
    print("\t7) Change the master key")
    print()
    print("Insert one option(q to escape): ", end="")

    while True:
        ans = input()
        if ans == "q":
            print("\nThank you for using password manager")
            sys.exit()
        if ans in {"1", "2", "3", "4", "5", "6"}:
            return int(ans)
        else:
            print("That's not a valid option. Please try again: ", end="")


def check_master_key(user_master_key, key, database: Database, salt):
    enc_master_key = database.load_from_database(key)[0][2]
    enc_user_mc = str(encryptors.key_encrypt_sha256(user_master_key + salt))
    if enc_master_key == enc_user_mc:
        return True
    else:
        return False


def get_public_master_key_from_db(database: Database):
    return database.load_from_database(MASTER_KEY_NAME_IN_DB)


def create_public_master_key(database: Database):
    print()
    print("Password manager".center(80, "-"), end="\n\n")
    print("Welcome to password manager.")
    print("As a first step, we need to create a master key to access all your passwords.")
    print(
        "Remember that this password must be really secure, and the only password you should remember"
    )
    while True:
        print()
        key = stdiomask.getpass("Please enter a secure password:")
        key2 = stdiomask.getpass("Please enter the same password again: ")
        if key == key2:
            break
        else:
            print("The passwords doesn't match")
    key = key + SALT
    enc_key = encryptors.key_encrypt_sha256(key)
    database.save_to_database(MASTER_KEY_NAME_IN_DB, "-", enc_key)
    print("\nMaster key added successfully")


def ask_user_for_master_key():
    print()
    print("Password manager".center(80, "-"), end="\n\n")
    print("Please insert the master key: ", end="")
    while True:
        master_key = stdiomask.getpass(prompt="")
        if check_master_key(master_key, MASTER_KEY_NAME_IN_DB, passwords_db, SALT):
            print("\nWelcome to the system.")
            return master_key
        else:
            print("The key is invalid, please enter a valid key: ", end="")


def get_a_password(database: Database, master_key):
    site = input("\nPlease, enter a site: ")
    site_encrypted = encryptors.field_encrypt(site, master_key)
    ans = database.load_from_database(site_encrypted)
    if not ans:
        print("There is no user and password for that site")
        return None
    for row in ans:
        site, user, password = encryptors.site_user_and_password_decrypt(row, master_key)
        print_record(site, user, password)
    pyperclip.copy(str(password))
    print("The password was copied to the clipboard")
    return ans


def print_record(site, user, password):
    print()
    print("-" * 40)
    print("Site:", site)
    print("User or mail:", user)
    print("Password:", password)
    print("-" * 40)


def create_new_password(database: Database, enc_master_key, site=None, user=None):
    if not site:
        site = input("\nPlease enter a site: ")
    if not user:
        user = input("Please enter a user or email: ")
    length = input("Enter a length for the password, or hit enter to default length of 20:")
    if length:
        length = int(length)
    else:
        length = 20
    password = encryptors.generate_password(length)
    enc_site, enc_user, enc_password = encryptors.site_user_and_password_encrypt(
        site, user, password, enc_master_key
    )
    ans = database.save_to_database(enc_site, enc_user, enc_password)
    if not ans:
        return
    print("\nYour generated password is:", password)
    pyperclip.copy(str(password))
    print("The password was copied to the clipboard")


def save_a_password(database: Database, enc_master_key):
    site = input("\nPlease enter a site: ")
    user = input("Please enter a user or email: ")
    password = input("Please enter a password: ")
    enc_site, enc_user, enc_password = encryptors.site_user_and_password_encrypt(
        site, user, password, enc_master_key
    )
    ans = database.save_to_database(enc_site, enc_user, enc_password)
    if not ans:
        return
    print("Your password was saved to the database")


def change_a_password(database: Database, enc_master_key):
    print("\nYou want to change one password of the database.")
    records = get_a_password(database, enc_master_key)
    if not records:
        return
    elif len(records) == 1:
        ans = input("Do you want to change this password?(yes/no): ")
        if ans == "yes":
            database.remove_from_database(records[0][0], records[0][1])
            site = encryptors.field_decrypt(records[0][0], enc_master_key)
            user = encryptors.field_decrypt(records[0][1], enc_master_key)
            create_new_password(database, enc_master_key, site, user)
            return
        else:
            print("Password wasn't changed.")
            return
    else:
        to_change = input(f"Please enter the number of record to change (1-{len(records)}):")
        while True:
            if to_change not in [str(x) for x in range(len(records) + 1)]:
                print("The value entered is not correct, please enter a valid record: ")
            else:
                break
        to_change = int(to_change) - 1
        database.remove_from_database(records[to_change][0], records[to_change][1])
        site = encryptors.field_decrypt(records[to_change][0], enc_master_key)
        user = encryptors.field_decrypt(records[to_change][1], enc_master_key)
        create_new_password(database, enc_master_key, site, user)
        return


def delete_a_password(database: Database, enc_master_key):
    print("\nYou want to delete one password of the database.")
    records = get_a_password(database, enc_master_key)
    if not records:
        return
    elif len(records) == 1:
        ans = input("Do you want to delete this record?(yes/no): ")
        if ans == "yes":
            database.remove_from_database(records[0][0], records[0][1])
            print("The password was deleted")
            return
        else:
            print("Nothing was deleted.")
            return
    else:
        to_delete = input(f"Please enter the number of record to delete (1-{len(records)}): ")
        while True:
            if to_delete not in [str(x) for x in range(len(records) + 1)]:
                print("The value entered is not correct, please enter a valid record: ")
            else:
                break
        to_delete = int(to_delete) - 1
        database.remove_from_database(records[to_delete][0], records[to_delete][1])
        print("The password was deleted")
        return


def print_all_users(database: Database, master_key):
    users = database.get_every_item_from_database()
    if len(users) < 2:  # Only public key record in the database
        print("\nThere is no record in the database")
        return
    for user in users:
        if user[0] == MASTER_KEY_NAME_IN_DB:
            continue
        site, user, password = encryptors.site_user_and_password_decrypt(user, master_key)
        print_record(site, user, password)


def change_master_key(database: Database, old_master_key):
    print("\nYou want to replace the master key.")
    answer = input("\nAre you sure you want to continue?:(yes/no): ")
    while True:
        if answer == "no":
            print("You decide not to change the master key.")
            return False
        if answer == "yes":
            break
        answer = input("Incorrect option, please enter a correct option: ")
    new_master_key = input("Please enter a secure password: ").strip()
    new_master_key_salted = new_master_key + SALT
    new_master_key_salted_encripted = encryptors.key_encrypt_sha256(new_master_key_salted)
    database.remove_from_database(MASTER_KEY_NAME_IN_DB, "-")
    database.save_to_database(MASTER_KEY_NAME_IN_DB, "-", new_master_key_salted_encripted)
    print("Master key replaced successfully")
    new_master_key_encripted = encryptors.key_encrypt_sha256(new_master_key)
    users = database.get_every_item_from_database()
    for user in users:
        if user[0] == MASTER_KEY_NAME_IN_DB:
            continue
        decrypted_pass = encryptors.field_decrypt(user[2], old_master_key)
        database.remove_from_database(user[0], user[1])
        new_password_encripted = encryptors.field_encrypt(decrypted_pass, new_master_key_encripted)
        database.save_to_database(user[0], user[1], new_password_encripted)
    print(
        "Your master key has been changed. All your passwords were encripted with the new master key"
    )
    return new_master_key_encripted


def ask_user_if_wants_to_continue_operating():
    while True:
        answer = input("\nDo you want to continue operating? (yes/no)[yes]: ")
        if answer == "no":
            print("Thank you for using password manager")
            sys.exit()
        elif answer == "yes" or answer == "":
            break
        else:
            print("Please enter a valid command.")


if __name__ == "__main__":
    public_master_key = get_public_master_key_from_db(passwords_db)
    if not public_master_key:
        create_public_master_key(passwords_db)
    master_key = ask_user_for_master_key()
    enc_master_key = encryptors.key_encrypt_sha256(master_key)
    while True:
        option_selected = menu()
        if option_selected == 1:
            get_a_password(passwords_db, enc_master_key)
        if option_selected == 2:
            create_new_password(passwords_db, enc_master_key)
        if option_selected == 3:
            save_a_password(passwords_db, enc_master_key)
        if option_selected == 4:
            change_a_password(passwords_db, enc_master_key)
        if option_selected == 5:
            delete_a_password(passwords_db, enc_master_key)
        if option_selected == 6:
            print_all_users(passwords_db, enc_master_key)
        if option_selected == 7:
            ans = change_master_key(passwords_db, enc_master_key)
            if ans != False:
                enc_master_key = ans
        ask_user_if_wants_to_continue_operating()
