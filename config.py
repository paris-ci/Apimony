# -*- coding:Utf-8 -*-
"""
renew-servers -- config
MODULE DESC 
"""
from __future__ import unicode_literals
import dialog; d = dialog.Dialog()

## MODIFIER A PARTIR DE CETTE LIGNE ##
useConfig = True

conf = {
"global" : {
    "user": "----x",
    "pass": "----"
},
"auto-renew" : {
    "blacklistServers": [],
    "coupon": "WayToDoor",
    "duration": "1"

}
}

## NE PAS TOUCHER APRES CETTE LIGNE ##
def get(var, domain="global", message = None, defaut=None):
    """
    Récupere le contenu de la variable depuis la config ou la demande à l'utilisateur.
    :param var: Nom de la variable à récupérer
    :param domain: Domaine dans la configuration
    :param defaut: Valeur par defaut si l'utilisateur n'etre rien
    :param message: Message à afficher pour demander le contenu de la variable
    :return: value
    """

    if useConfig:
        try:
            return conf[domain][var]
        except KeyError:
            pass
        except ValueError:
            pass

    exit = False
    while not exit:
        if message:
            question = message
        else:
            question = "Veuillez entrer une valeur pour " + var
        if defaut:
            question += " (" + str(defaut) +") >"
            val = d.inputbox(question, init=str(defaut))
        else:
            code, val = d.inputbox(question)

        return val

