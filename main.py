#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import urllib.request
import json
import os
import time
from collections import OrderedDict
from bs4 import BeautifulSoup
import requests
import tkinter as tk
from tkinter import messagebox, ttk
import pyperclip

dir_url = 'http://www.t2c.fr/admin/synthese?SERVICE=page&p=17732927961956390&noline='
stop_url = 'http://www.t2c.fr/admin/synthese?SERVICE=page&p=17732927961956392&numeroroute='

lines = {
    'A': '11821953316814895',
    'B': '11821953316814897',
    'C': '11821953316814915',
    '3': '11821953316814882',
    '4': '11821953316814888',
    '5': '11821953316814889',
    '7': '11821953316814891',
    '8': '11821953316814892',
    '9': '11821953316814893',
    '10': '11821953316814874',
    '12': '11821953316814875',
    '13': '11821953316814876',
    '20': '11821953316814877',
    '21': '11821953316814878',
    '22': '11821953316814879',
    '23': '11822086460801028',
    '24': '11821953316814913',
    '25': '11822086460801025',
    '26': '11821953316814880',
    '27': '11821953316814881',
    '28': '11822086460801030',
    '31': '11821953316814883',
    '32': '11821953316814884',
    '33': '11821953316814914',
    '34': '11821953316814885',
    '35': '11821953316814886',
    '36': '11821953316814887',
    '37': '11822086460801032'
}


def get_line_data(url):
    item_list = OrderedDict()
    req = urllib.request.urlopen(url)
    soup = BeautifulSoup(req, from_encoding='utf-8', features='html.parser')

    for item in soup.find_all('option')[1:]:
        item_name = item.text.strip()
        item_num = item['value']
        item_list[item_name] = item_num

    return item_list


def fill_json():
    data = {'lines': []}

    for line_name, line_num in lines.items():
        print(f'Traitement de la ligne {line_name}')
        line_data = {'line_name': line_name, 'line_num': line_num, 'directions': []}

        line_dir = get_line_data(dir_url + line_num)
        for dir_name, dir_num in line_dir.items():
            dir_data = {'dir_name': dir_name, 'dir_num': dir_num, 'stops': []}

            line_stop = get_line_data(stop_url + dir_num)
            for stop_name, stop_num in line_stop.items():
                dir_data['stops'].append({'stop_name': stop_name, 'stop_num': stop_num})

            line_data['directions'].append(dir_data)

        data['lines'].append(line_data)

    with open('t2c_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def test_api(stop_id):
    url = f"http://88.151.197.193:2001/horaire/{stop_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Erreur lors de la requête : {e}"}
    except json.JSONDecodeError:
        return {"error": "Erreur lors du décodage de la réponse JSON"}
    except Exception as e:
        return {"error": f"Une erreur inattendue s'est produite : {e}"}


def afficher_horaires(data):
    fenetre_resultats = tk.Toplevel()
    fenetre_resultats.title("Résultats")
    fenetre_resultats.geometry("500x300")

    text_widget = tk.Text(fenetre_resultats, wrap=tk.WORD)
    text_widget.pack(expand=True, fill=tk.BOTH)

    if "error" in data:
        text_widget.insert(tk.END, f"Erreur : {data['error']}\n")
    else:
        text_widget.insert(tk.END, f"Horaires pour l'arrêt :\n")
        text_widget.insert(tk.END, "-" * 50 + "\n")

        if "departures" in data:
            for departure in data["departures"]:
                text_widget.insert(tk.END,
                                   f"Ligne {departure['ligne']:3} | {departure['destination']:20} | Départ : {departure['depart']:10} | {departure['info']}\n")

        if "perturbation" in data and data["perturbation"]:
            text_widget.insert(tk.END, "\n⚠️ ATTENTION :\n")
            text_widget.insert(tk.END, data["perturbation"] + "\n")

    text_widget.config(state=tk.DISABLED)


def horaire_bus():
    fenetre_horaire = tk.Toplevel()
    fenetre_horaire.title("Horaire arrêt")
    fenetre_horaire.geometry("200x100")

    id_arret = tk.Entry(fenetre_horaire, width=30)
    id_arret.pack(pady=10)

    def send_request():
        stop_id = id_arret.get()
        if stop_id:
            data = test_api(stop_id)
            afficher_horaires(data)
        else:
            messagebox.showerror("Erreur", "Veuillez entrer un ID d'arrêt")

    button_send = tk.Button(fenetre_horaire, text="OK", command=send_request)
    button_send.pack(pady=10)


def afficher_id_arrets():
    with open('t2c_data.json', 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    fenetre_arrets = tk.Toplevel()
    fenetre_arrets.title("ID des arrêts")
    fenetre_arrets.geometry("600x400")

    frame = tk.Frame(fenetre_arrets)
    frame.pack(expand=True, fill=tk.BOTH)

    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(frame, columns=('Ligne', 'Direction', 'Arrêt', 'ID'), show='headings',
                        yscrollcommand=scrollbar.set)
    tree.heading('Ligne', text='Ligne')
    tree.heading('Direction', text='Direction')
    tree.heading('Arrêt', text='Arrêt')
    tree.heading('ID', text='ID')
    tree.column('Ligne', width=50)
    tree.column('Direction', width=150)
    tree.column('Arrêt', width=150)
    tree.column('ID', width=150)
    tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    scrollbar.config(command=tree.yview)

    def copier_id(event):
        item = tree.selection()[0]
        id_arret = tree.item(item, "values")[3]
        pyperclip.copy(id_arret)
        tk.messagebox.showinfo("Copié", f"L'ID {id_arret} a été copié dans le presse-papiers.")

    tree.bind("<Double-1>", copier_id)

    for line in data['lines']:
        for direction in line['directions']:
            for stop in direction['stops']:
                tree.insert('', 'end',
                            values=(line['line_name'], direction['dir_name'], stop['stop_name'], stop['stop_num']))

    instructions = tk.Label(fenetre_arrets, text="Double-cliquez sur une ligne pour copier l'ID de l'arrêt")
    instructions.pack(pady=5)


def main():
    fenetre_menu = tk.Tk()
    fenetre_menu.title("T2C Bus")
    fenetre_menu.geometry("200x200")

    button_horaire = tk.Button(fenetre_menu, text="Prochain bus à l'arrêt", command=horaire_bus)
    button_horaire.pack(pady=5)

    button_arret = tk.Button(fenetre_menu, text="ID des arrêts", command=afficher_id_arrets)
    button_arret.pack(pady=5)

    button_update = tk.Button(fenetre_menu, text="Mettre à jour les données", command=fill_json)
    button_update.pack(pady=5)

    fenetre_menu.mainloop()


if __name__ == "__main__":
    if not os.path.exists('t2c_data.json'):
        fill_json()
    main()
