# -*- coding:Utf-8 -*-
# !/usr/bin/env python3.5
"""
renew-servers -- util
MODULE DESC 
"""
# Constants #
from __future__ import unicode_literals

import re
import time
import webbrowser

import config
import dialog
from HarmonAPy.HarmonAPy import HarmonAPy

__author__ = "Arthur — paris-ci"
__licence__ = "WTFPL — 2016"

api = HarmonAPy(config.get("user", message="Entrez votre nom d'utilisateur"), config.get("pass", message="Entrez votre cle d'API"), ssl=False)
d = dialog.Dialog()


def billInfo(tag, bills_dict):
    transactions = ""
    i = 0
    for transaction in bills_dict[tag]["transactions"]:
        transactions += "\n\t{i} -> Date : {date}| Montant : {amount} | Type : {type} | Id : {id}".format(
            **{"i": i + 1, "date": transaction["date"], "amount": transaction["amount"], "type": transaction["type"], "id": transaction["id"]})
        i += 1
    d.msgbox(
        """Facture cree le {date},
        Montant paye : {paid}/{total}
        Annulee      : {cancelled}
        Expiree      : {expired}
        Transactions : {transactions}
        URL          : https://www.harmony-hosting.com/store/bill/{id}/show
        """.format(**{
            "date"        : bills_dict[tag]["created_at"],
            "paid"        : bills_dict[tag]["payed_amount"],
            "total"       : bills_dict[tag]["price"],
            "cancelled"   : bills_dict[tag]["cancelled"],
            "expired"     : bills_dict[tag]["expired"],
            "transactions": transactions,
            "id"          : tag
            }), width=100, height=15, title="Facture " + str(tag))


def renewServer(veid):
    duree_renew = config.get("duration", domain="auto-renew", message="Veuillez entrer la duree de location en mois : 1,3,6,12", defaut="1")
    duree_renew = int(duree_renew)
    coupon = config.get("coupon", domain="auto-renew", message="Disposez-vous d'un coupon de reduction ?", defaut="")
    d.gauge_start()
    d.gauge_update(0, text="Creation d'une facture", update_text=True)
    bill = api.post("/bills")
    d.gauge_update(30, text="Ajout du serveur a la facture", update_text=True)
    api.post("/bills/{id_bill}/items/servers/renew".format(**{"id_bill": bill["id"]}),
             data={'duration': duree_renew, "veid": veid, "coupon": coupon})
    time.sleep(.5)
    d.gauge_update(90, text="Generation de l'URL de la facture", update_text=True)
    url = "https://www.harmony-hosting.com/store/bill/{id_bill}/show".format(**{"id_bill": bill["id"]})
    time.sleep(.5)
    d.gauge_update(100, text="Finalisation", update_text=True)
    time.sleep(.5)
    webbrowser.open(url, new=0, autoraise=True)
    d.gauge_stop()
    d.msgbox("Termine ! Allez payer votre facture : \n" + url)


def serverPref(veid):
    exit_ = False
    modified = False
    while not exit_:
        code, tag = d.menu("Choissisez une action :", choices=[
            ("(1)", "Demarrer le serveur"),
            ("(2)", "Aretter le serveur"),
            ("(3)", "Redemarrer le serveur"),
            ("(4)", "Changer le mot de passe du serveur"),
            ("(5)", "Configurer le FW"),
            ("(10)", "Reinstaller le serveur"),
            ("(11)", "Renouveler le serveur"),
            ("(X)", "Quitter le menu")], width=100, menu_height=15)
        if code != d.OK:
            exit_ = True
        else:
            if tag == "(1)":
                d.msgbox("Demande de demarrage envoyee : " + str(api.post("/servers/{veid}/start".format(**{"veid": veid}))))
            elif tag == "(2)":
                d.msgbox("Demande d'arret envoyee : " + str(api.post("/servers/{veid}/stop".format(**{"veid": veid}))))
            elif tag == "(3)":
                d.msgbox("Demande de redemarrage envoyee : " + str(api.post("/servers/{veid}/reboot".format(**{"veid": veid}))))
            elif tag == "(4)":
                code, password = d.passwordbox(
                    "Entrez un mot de passe de plus de 8 caracteres, contenant AU MINIMUM une lettre majuscule, une lettre minuscule, et un chiffre")
                if code != d.OK:
                    d.msgbox("Changement de mot de passe annule")
                elif re.match("^(?=.*?[A-Z])(?=(.*[a-z]){1,})(?=(.*[\d]){1,})(?!.*\s).{8,}$", password):
                    api.post("/servers/{veid}/password".format(**{"veid": veid}), {"password": password})
                    d.msgbox("Changement de mot de passe effecute")
                else:
                    d.msgbox("Mot de passe incorrect: il ne respecte pas les conditions enoncees")
            elif tag == "(5)":
                modified = configServerFirewall(veid)
            elif tag == "(10)":
                modified = reinstallServer(veid)
            elif tag == "(11)":
                renewServer(veid)
                modified = True
            elif tag == "(X)":
                exit_ = True
    return modified


def configServerFirewall(veid):
    d.gauge_start()
    d.gauge_update(0, text="Recuperation des regles actuelles", update_text=True)
    rules = sorted(api.get("/servers/{veid}/firewall/rules".format(**{"veid": veid})))
    rules_dict = {}
    rules_parsed = []
    exit_ = False
    i = 0
    for rule in rules:
        d.gauge_update(10 + int((float(i) / float(len(rules))) * 90), text="Recuperation regle " + str(rule), update_text=True)

        rules_dict.update({rule: api.get("/servers/{veid}/firewall/rules/{rule}".format(**{"veid": veid, "rule": rule}))})
        rules_parsed += [(str(rule), rules_dict[rule]["protocol"] + "-" + rules_dict[rule]["destination_port"] + " = " + rules_dict[rule]["action"])]

        i += 1
    if not len(rules_parsed):
        rules_parsed = [("21", "Aucune regle definie")]

    rules_parsed += [("A", "Ajouter une regle")]
    d.gauge_stop()
    while not exit_:
        code, rule = d.menu("Liste des regles :", choices=rules_parsed, width=100, menu_height=22)
        if code != d.OK:
            exit_ = True
        else:
            if str(rule).isdigit() and int(rule) <= 20:
                code, action = d.menu(
"""Protocole : {protocol}
Prioritee : {priority}
IP source: {source}
Port source : {source_port}
Port destination :{destination_port}
Action : {action}""".format(
                        **rules_dict[int(rule)]), choices=[("(1)", "Supprimer la regle"),
                                                           ("(2)", "Modifier la regle"),
                                                           ("(X)", "Retour au menu precedent")])
                if code == d.OK:
                    if action == "(1)":
                        d.infobox("Supression de la regle...")
                        api.delete("/servers/{veid}/firewall/rules/{rule}".format(**{"veid" : veid, "rule": rule}))
                        time.sleep(.25)
                        d.msgbox("Regle suprimee " )
                        return True
                    elif action == "(2)":
                        data_dict={}
                        rule = int(rule)
                        proto_dispos = ["udp", "tcp", "icmp", "ipv4"]
                        choices_list = []
                        proto_dispos.remove(rules_dict[rule]["protocol"])
                        choices_list.append((rules_dict[rule]["protocol"], "Protocole " + rules_dict[rule]["protocol"], True))
                        for proto_dispo in proto_dispos:
                            choices_list.append((proto_dispo, "Protocole " + proto_dispo, False))
                        code, data_dict["protocol"] = d.radiolist("Quel protocole doit etre definit pour la regle ?", choices=choices_list)
                        if code != d.OK:
                            d.msgbox("Annulation...")
                            return False
                        data_dict["priority"] = rules_dict[rule]["priority"]
                        code, data_dict["block_source"] = d.inputbox("Veuillez entrer le block source (rien pour tout)", init=rules_dict[rule]["source"])
                        if not data_dict["block_source"]:
                            data_dict.pop("block_source")
                        if code != d.OK:
                            d.msgbox("Annulation...")
                            return False
                        if data_dict["protocol"] in ["udp", "tcp"]:
                            code, data_dict["source_port"] = d.inputbox("Veuillez entrer le port source (* pour tout)", init=rules_dict[rule]["source_port"])
                            if code != d.OK:
                                d.msgbox("Annulation...")
                                return False
                            code, data_dict["dest_port"] = d.inputbox("Veuillez entrer le port destination (* pour tout)", init=rules_dict[rule]["destination_port"])
                            if code != d.OK:
                                d.msgbox("Annulation...")
                                return False

                        code, data_dict["action"] = d.radiolist("Autoriser ou interdire ?", choices=[("permit", "Autoriser", rules_dict[rule]["action"] == "permit"), ("deny", "Refuser", rules_dict[rule]["action"] == "deny")])
                        d.gauge_start()
                        d.gauge_update(0, text="Supression de l'ancienne regle", update_text=True)
                        api.delete("/servers/{veid}/firewall/rules/{rule}".format(**{"veid" : veid, "rule": rule}))
                        time.sleep(.25)
                        d.gauge_update(50, text="Creation de la nouvelle regle", update_text=True)
                        api.post("/servers/{veid}/firewall/rules".format(**{"veid" : veid}), data=data_dict)
                        time.sleep(.25)
                        d.gauge_update(100, text="Finalisation", update_text=True)
                        time.sleep(.5)
                        d.msgbox("Regle modifiee")
                        return True
            elif rule == "A":
                data_dict={}
                proto_dispos = ["udp", "tcp", "icmp", "ipv4"]
                choices_list = []
                for proto_dispo in proto_dispos:
                    choices_list.append((proto_dispo, "Protocole " + proto_dispo, False))
                code, data_dict["protocol"] = d.radiolist("Quel protocole doit etre definit pour la regle ?", choices=choices_list)
                if code != d.OK:
                    d.msgbox("Annulation...")
                    return False
                done = False
                while not done:
                    code, data_dict["priority"] = d.rangebox(text="Prioritee de la regle ?", min=0, max=19, init=0, width=100)
                    if code != d.OK:
                        d.msgbox("Annulation...")
                        return False
                    if data_dict["priority"] in rules_dict.keys():
                        d.msgbox("Erreur : la regle existe deja !")
                    else:
                        data_dict["priority"] = str(data_dict["priority"])
                        done = True
                code, data_dict["block_source"] = d.inputbox("Veuillez entrer le block source (rien pour tout)", init="")
                if not data_dict["block_source"]:
                    data_dict.pop("block_source")
                if code != d.OK:
                    d.msgbox("Annulation...")
                    return False
                if data_dict["protocol"] in ["udp", "tcp"]:
                    code, data_dict["source_port"] = d.inputbox("Veuillez entrer le port source (* pour tout)", init="*")
                    if code != d.OK:
                        d.msgbox("Annulation...")
                        return False
                    code, data_dict["dest_port"] = d.inputbox("Veuillez entrer le port destination (* pour tout)", init="*")
                    if code != d.OK:
                        d.msgbox("Annulation...")
                        return False

                code, data_dict["action"] = d.radiolist("Autoriser ou interdire ?", choices=[("permit", "Autoriser", True), ("deny", "Refuser", False)])
                d.infobox("Creation de la nouvelle regle")
                api.post("/servers/{veid}/firewall/rules".format(**{"veid" : veid}), data=data_dict)
                time.sleep(.5)
                d.msgbox("Regle cree")
                return True
            else:
                return False

    return False


def reinstallServer(veid):
    d.gauge_start()
    d.gauge_update(0, text="Recuperation de la liste des templates", update_text=True)
    templates = api.get("/servers/{veid}/templates")
    d.gauge_update(10, text="Parsing de la liste des templates", update_text=True)
    list_templates = []
    for template in templates:
        list_templates.append((template["system_name"], template["name"]))

    code, template = d.menu("Choissisez le template adequat pour la reinstallation :", choices=list_templates, width=40, menu_height=30)
    if code != d.OK:
        d.msgbox("Reinstallation anulee")
        return False
    else:
        code, password = d.passwordbox(
            "Entrez un mot de passe de plus de 8 caracteres, contenant AU MINIMUM une lettre majuscule, une lettre minuscule, et un chiffre")
        if code != d.OK:
            d.msgbox("Reinstallation anulee")
            return False
        elif re.match("^(?=.*?[A-Z])(?=(.*[a-z]){1,})(?=(.*[\d]){1,})(?!.*\s).{8,}$", password):
            d.gauge_update(50, text="Reinstallation en cours... Ca peut prendre un petit bout de temps, veuillez patienter.", update_text=True)
            rep = api.post("/servers/{veid}/reinstall".format(**{"veid": veid}), {"password": password, "template": template})
            d.gauge_update(100, text="Finalisation", update_text=True)
            time.sleep(.5)
            d.msgbox("Reinstallation terminee : " + str(rep))
            return True
        else:
            d.msgbox("Mot de passe incorrect.")
            return False


def serverInfo(tag, servers_dict):
    srv = servers_dict[tag]

    pref = not d.yesno(str(
        """IPv4 serveur : {IP4}
        IPV6 serveur : {IP6}

        Verouille/Expire : {locked}
        Date expiration : {expiration}

        DNS cloudcraft : {cloudcraft}
        Reverse DNS IPV4 : {reverse4}
        Reverse DNS IPV4 : {reverse6}

        Nombres de coeurs : {cores}
        Espace disque : {disk}G
        Memoire RAM : {ram}MB
        """.format(**{
            "IP4"       : srv["ip"]["ip4"],
            "IP6"       : srv["ip"]["ip6"],
            "locked"    : srv["is_locked"],
            "expiration": srv["expiration"],
            "cloudcraft": srv["dns"],
            "reverse4"  : srv.get("reverse4", "Aucun reverse DNS4"),
            "reverse6"  : srv.get("reverse6", "Aucun reverse DNS6"),
            "cores"     : srv["plan"]["cores"],
            "disk"      : srv["plan"]["disk"],
            "ram"       : srv["plan"]["memory"]
            })), width=100, height=22, title="Serveur " + str(tag), yes_label="OK, retour a la liste", no_label="Preferences") == d.OK
    if pref:

        return serverPref(srv["veid"])
    else:
        return False