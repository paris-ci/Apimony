#!/usr/bin/env python2.7
# encoding: utf-8

"""
renew-servers -- main.py
Script pour renouvleler tout les serveurs d'un coup.
"""
from __future__ import unicode_literals

import os
import sys

from util import *

__author__ = "Arthur — paris-ci"
__licence__ = "WTFPL — 2016"


def main():
    ver = api.get("/version")
    try:
        d.msgbox("Bienvenue ! \n Connexion initiee avec succes : la version de l\'API de HarmonyHosting est : {0}".format(ver["version"]))
    except TypeError:
        d.msgbox("Erreur de connexion a l'API : \n" + ver)
        sys.exit(1)

    exit_ = False
    while not exit_:
        code, tag = d.menu("Choissisez une action :", choices=[
            ("(1)", "Renouveller tout les serveurs"),
            ("(2)", "Voir les factures"),
            ("(3)", "Voir les serveurs"),
            ("(4)", "Appel a l'API personalise GET"),
            ("(X)", "Quitter le programme")])
        if code != d.OK:
            exit_ = True
        else:
            if tag == "(1)":
                renewall()
            elif tag == "(2)":
                showBills()
            elif tag == "(3)":
                showServers()
            elif tag == "(4)":
                code, req = d.inputbox("GET")
                d.msgbox(str(api.get(str(req))), width=100, height=22, title=str(req))
            elif tag == "(X)":
                exit_ = True


def renewall():
    blacklist = config.get("blacklistServers", domain="auto-renew", message="Veuillez entrer le/les serveurs que vous souhaitez ignorer.",
                           defaut="[]")
    blacklist = list(blacklist)
    duree_renew = config.get("duration", domain="auto-renew", message="Veuillez entrer la duree de location en mois : 1,3,6,12", defaut="1")
    duree_renew = int(duree_renew)
    coupon = config.get("coupon", domain="auto-renew", message="Disposez-vous d'un coupon de reduction ?", defaut="")
    to_renew = []
    servers_gauge = []
    i = 0
    for server in api.get("/servers"):
        if not server in blacklist:
            to_renew.append(server)
            servers_gauge.append(("Serveur " + str(server), "-0"))
            print(servers_gauge)

    def generateGaugeList(servers_gauge, ls="0", cf="-0", ln="-0"):
        return [("Recuperation liste serveurs", ls),
                ("Creation facture", cf),
                ("", "8")
                ] + servers_gauge + [
                   ("", "8"),
                   ("Generation du lien", ln)]

    d.mixedgauge("Creation de la facture en cours...", percent=10, elements=(generateGaugeList(servers_gauge)))
    bill = api.post("/bills")
    # print("Nouvelle facture :" + str(bill["id"]))
    for server in to_renew:
        d.mixedgauge("Creation de la facture en cours...", percent=(20 + int(float(i) / float(len(to_renew)) * 70)),
                     elements=(generateGaugeList(servers_gauge, cf="0")))
        api.post("/bills/{id_bill}/items/servers/renew".format(**{"id_bill": bill["id"]}),
                 data={'duration': duree_renew, "veid": server, "coupon": coupon})
        servers_gauge[i] = ("Serveur " + str(server), "0")
        i += 1
        time.sleep(.5)

    d.mixedgauge("Creation de la facture en cours...", percent=90, elements=(generateGaugeList(servers_gauge, cf="0")))
    url = "https://www.harmony-hosting.com/store/bill/{id_bill}/show".format(**{"id_bill": bill["id"]})
    time.sleep(.5)
    d.mixedgauge("Creation de la facture en cours...", percent=100, elements=(generateGaugeList(servers_gauge, cf="0", ln="0")))
    time.sleep(.5)
    webbrowser.open(url, new=0, autoraise=True)
    d.msgbox("Termine ! Allez payer votre facture : \n" + url)


def showBills():
    d.gauge_start()
    bills = api.get("/bills")
    bills_parsed = []
    bills_dict = {}
    i = 0
    for bill in bills:
        bills_dict.update({bill: api.get("/bills/" + str(bill))})
        i += 1

        pourcentage = int((i / float(len(bills))) * 100)
        d.gauge_update(pourcentage, text="Facture " + str(bill), update_text=True)

        if bills_dict[bill]["expired"]:
            intitule = "Facture expiree"
        elif bills_dict[bill]["cancelled"]:
            intitule = "Facture anulee"
        elif bills_dict[bill]["payed_amount"] == bills_dict[bill]["price"]:
            intitule = "Facture payee"
        else:
            intitule = "Facture"
        bills_parsed += [(str(bill), intitule)]

    exit_code = d.gauge_stop()
    exit_ = False
    while not exit_:
        code, tag = d.menu("Liste des factures :", choices=bills_parsed)
        if code != d.OK:
            exit_ = True
        else:
            billInfo(int(tag), bills_dict)


def showServers():
    d.gauge_start()
    servers = api.get("/servers")
    servers_parsed = []
    servers_dict = {}
    i = 0
    for server in servers:
        servers_dict.update({server: api.get("/servers/" + str(server))})
        i += 1

        pourcentage = int((i / float(len(servers))) * 100)
        d.gauge_update(pourcentage, text="Serveur " + str(server), update_text=True)

        if servers_dict[server]["is_locked"]:
            intitule = "VERR " + servers_dict[server]["dns"]
        else:
            intitule = servers_dict[server]["dns"]
        servers_parsed += [(str(server), intitule)]

    exit_code = d.gauge_stop()
    exit_ = False
    while not exit_:
        code, tag = d.menu("Liste des serveurs :", choices=servers_parsed)
        if code != d.OK:
            exit_ = True
        else:
            tag = int(tag)

            if serverInfo(tag, servers_dict):
                return


try:
    if __name__ == '__main__':
        main()
except Exception as e:
    os.system("clear")
    print("===== " + str(e) + " ====")
    raise e